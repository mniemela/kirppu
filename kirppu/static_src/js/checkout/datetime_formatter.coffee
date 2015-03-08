# Date locale formatter wrapper.
# init() must be called before using this class. Giving arguments to init() or setting locales and timeZone
# by hand before calling init() gives same result.
class @DateTimeFormatter
  # Name of the time zone used in formatting of times / timestamps.
  # (Not currently used.)
  @timeZone = null

  # Locale name used to format dates, times and timestamps.
  @locales = null

  # Initialize DateTimeFormatter.
  # @param locales [optional] If given with timeZone, used to assign `locales`.
  # @param timeZone [optional] If given with locales, used to assign `timeZone`.
  @init: (locales=undefined, timeZone=undefined) ->
    if locales? and timeZone?
      @locales = locales
      @timeZone = timeZone
    moment.locale(@locales)

  # Format a date to string.
  @date: (value) -> moment(value).format("L")

  # Format a time to string.
  @time: (value) -> moment(value).format("LTS")

  # Format a time stamp to string.
  @datetime: (value) -> moment(value).format("L LTS")
