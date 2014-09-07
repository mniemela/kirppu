
class @DateTimeFormatter
  # Name of the time zone used in formatting of times / timestamps.
  @timeZone = null

  # Locale name used to format dates, times and timestamps.
  @locales = null

  # Yield options passed to Date format functions.
  # @private
  @_createDateOptions: () ->
    return timeZone: DateTimeFormatter.timeZone

  # Test if given Date function supports locales.
  # @param fn [String] Function name, such as "toLocaleString".
  # @return [Boolean] True if the function supports locales, false if not.
  @_dateSupportsLocales: (fn) ->
    # If calling Date function fn raises error about invalid locale string, the locale support exists.
    # If unsupported, the argument is going to be ignored.
    try
      new Date()[fn]("i")
    catch e
      return e.name is "RangeError"
    return false

  # Build dictionary of function names to boolean value of whether the function supports localizing or not.
  @_buildSupport: (args...) ->
    r = {}
    for arg in args
      r[arg] = @_dateSupportsLocales(arg)
    return r

  @_dateSupport: @_buildSupport("toLocaleDateString", "toLocaleTimeString", "toLocaleString")

  # Helper function for calling locale-aware toLocale*String functions of date objects.
  # If the function does not support locales, their un-aware versions are called instead.
  #
  # @param dateObj [Date] Object to call the function on.
  # @param fn [String] Function name to call.
  # @return [String] Locale-formatted string.
  # @private
  @_callDateLocale: (dateStr, fn) ->
    dateObj = new Date(dateStr)
    if @_dateSupport[fn]
      return dateObj[fn](@locales, @_createDateOptions())
    else
      return dateObj[fn]()

  # Format a date to string.
  @date: (value) -> @_callDateLocale(value, "toLocaleDateString")

  # Format a time to string.
  @time: (value) -> @_callDateLocale(value, "toLocaleTimeString")

  # Format a time stamp to string.
  @datetime: (value) -> @_callDateLocale(value, "toLocaleString")
