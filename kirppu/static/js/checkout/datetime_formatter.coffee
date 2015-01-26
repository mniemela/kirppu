# Date locale formatter wrapper.
# init() must be called before using this class. Giving arguments to init() or setting locales and timeZone
# by hand before calling init() gives same result.
class @DateTimeFormatter
  # Name of the time zone used in formatting of times / timestamps.
  @timeZone = null

  # Locale name used to format dates, times and timestamps.
  @locales = null

  # Yield options passed to Date format functions.
  # @private
  @_createDateOptions: () ->
    return timeZone: @constructor.timeZone

  # Test if given Date function supports locales.
  # @param fn [String] Function name, such as "toLocaleString".
  # @return [Integer] 2 if function supports locales with timezones. 1 if only locales. 0 if neither.
  @_dateSupportsLocales: (fn) ->
    # If calling Date function fn raises error about invalid locale string, the locale support exists.
    # If unsupported, the argument is going to be ignored.
    try
      new Date()[fn]("i")
    catch e
      # This is expected, when locales support exist.
      if e.name is "RangeError"
        try
          # This fails for "unknown timezone" if timezones are not supported.
          new Date()[fn](@locales, timeZone: @timeZone)
        catch e
          # No TZ support.
          return 1 if e.name is "RangeError"
        # TZ and locales support.
        return 2
    # No support at all.
    return 0

  # Build dictionary of function names to boolean value of whether the function supports localizing or not.
  @_buildSupport: (args...) ->
    r = {}
    for arg in args
      r[arg] = @_dateSupportsLocales(arg)
    return r

  # Initialize DateTimeFormatter.
  # @param locales [optional] If given with timeZone, used to assign `locales`.
  # @param timeZone [optional] If given with locales, used to assign `timeZone`.
  @init: (locales=undefined, timeZone=undefined) ->
    if locales? and timeZone?
      @locales = locales
      @timeZone = timeZone
    @_dateSupport = @_buildSupport("toLocaleDateString", "toLocaleTimeString", "toLocaleString")

  @_dateSupport: null

  # Helper function for calling locale-aware toLocale*String functions of date objects.
  # If the function does not support locales, their un-aware versions are called instead.
  #
  # @param dateObj [Date] Object to call the function on.
  # @param fn [String] Function name to call.
  # @return [String] Locale-formatted string.
  # @private
  @_callDateLocale: (dateStr, fn) ->
    dateObj = new Date(dateStr)
    supported = @_dateSupport[fn]
    if supported == 2
      return dateObj[fn](@locales, @_createDateOptions())
    else if supported == 1
      return dateObj[fn](@locales)
    else
      return dateObj[fn]()

  # Format a date to string.
  @date: (value) -> @_callDateLocale(value, "toLocaleDateString")

  # Format a time to string.
  @time: (value) -> @_callDateLocale(value, "toLocaleTimeString")

  # Format a time stamp to string.
  @datetime: (value) -> @_callDateLocale(value, "toLocaleString")
