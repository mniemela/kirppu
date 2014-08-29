# Base class for operation modes.
#
# @abstract
class @CheckoutMode

  # @param switcher [ModeSwitcher] ModeSwitcher to use.
  # @param config [Config, optional] Configuration instance override.
  constructor: (switcher, config) ->
    @switcher = switcher
    @cfg = if config then config else CheckoutConfig

  # Title to display in this mode.
  #
  # @return [String] Title string.
  title: -> "[unknown mode]"

  # Subtitle to display in this mode.
  #
  # @return [String, null] Subtitle string, if needed.
  subtitle: -> null

  # Return a list of <th> elements for the receipt.
  columns: -> []

  # Called after switching to this mode.
  enter: -> do @clearReceipt

  # Called after switching out of this mode.
  exit: ->

  # Return an Array where each element is a [prefix, handler function]
  # array. The handler will be called with (code, prefix) where code is
  # the input without the prefix.
  #
  # Would use an Object instead of an Array of Arrays if literal objects
  # with dynamic property names were supported.
  #
  # @return [Array] Mapping from prefixes to handler functions.
  actions: -> [["", ->]]

  # Empty the receipt and create new headers.
  clearReceipt: ->
    @cfg.uiRef.receiptTable.empty().append(
      $("<thead>").append($("<tr>").append(@columns())),
      @cfg.uiRef.receiptResult.empty(),
    )
    @cfg.uiRef.receiptSum.empty()
