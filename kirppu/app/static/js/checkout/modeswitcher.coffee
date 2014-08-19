# Safely set or remove class to/from element.
#
# @param element [$] Element to adjust.
# @param cls [String] CSS Class name to adjust.
# @param enabled [Boolean] Whether the class should exist in the element.
# @return [$] The element.
setClass = (element, cls, enabled) ->
  if element.hasClass(cls) != enabled
    if enabled
      element.addClass(cls)
    else
      element.removeClass(cls)
  return element

# Class for switching CheckoutModes.
class @ModeSwitcher

  # Map of entry point names to CheckoutModes.
  @entryPoints = {}

  # Register entry point with name.
  #
  # @param name [String] Name of the entry point.
  # @param mode [CheckoutMode] Entry point, CheckoutMode subclass.s
  @registerEntryPoint: (name, mode) ->
    if name of @entryPoints
      console.error("Name '#{ name }' was already registered for '#{ @entryPoints[name].name }' while registering '#{ mode.name }'.")
      return
    @entryPoints[name] = mode
    return

  # @param config [Config, optional] Configuration instance override.
  constructor: (config) ->
    @cfg = if config then config else CheckoutConfig
    @_currentMode = null
    @_bindMenu(ModeSwitcher.entryPoints)

  # Start default mode operation.
  startDefault: ->
    @switchTo(ModeSwitcher.entryPoints["counter_validation"])

  # Switch to new mode. This is called by modes.
  #
  # @param mode [CheckoutMode, class] Class of new mode.
  switchTo: (mode) ->
    if @_currentMode?
      if not @_currentMode.onPreUnBind()
        throw new Error(@_currentMode.name + " refused to stop.")

      @_currentMode.unbind()
      @_currentMode = null
    newMode = new mode(@, @cfg)
    if not newMode.onPreBind()
      return
    newMode.bind()
    newMode.clearReceipt()
    @_currentMode = newMode
    return

  # Get name of currently active mode.
  #
  # @return [String] Mode name.
  currentMode: -> if @_currentMode? then @_currentMode.constructor.name else null

  # Bind mode switching menu items.
  _bindMenu: (entryPoints) ->
    # For all menu-items that have data-entrypoint attribute defined, if the
    # name defined by that attribute is found in entryPoints, add
    # click-handler that will switch mode to the mode defined by the value in
    # entryPoints dictionary.
    menu = @cfg.uiRef.modeMenu
    items = menu.find("[data-entrypoint]")
    for itemDom in items
      item = $(itemDom)
      entryPointName = item.attr("data-entrypoint")
      if entryPointName of entryPoints
        entryPoint = entryPoints[entryPointName]

        # As entryPoint -variable is somehow shared across all iterations of
        # the for-loop, forcing own variable per iteration with extra function
        # wrap that is called immediately with current values.
        ((this_, ep) ->
          item.click(() ->
            console.log("Changing mode from menu to " + ep.name)
            this_.switchTo(ep)
          )
        )(@, entryPoint)
      else
        console.warn("Entry point '#{ entryPointName }' could not be found from registered entry points. Source:")
        console.log(itemDom)
    return

  # Enable or disable mode switching menu.
  #
  # @param enabled [Boolean] If true, menu will be enabled. If false, menu will be disabled.
  setMenuEnabled: (enabled) ->
    menu = @cfg.uiRef.modeMenu
    setClass(menu, "disabled", not enabled)
    setClass(menu.find("a:first"), "disabled", not enabled)
