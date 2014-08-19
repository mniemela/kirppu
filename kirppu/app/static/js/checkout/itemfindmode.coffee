class @ItemFindMode extends ItemCheckoutMode

  title: -> "Find"
  subtitle: -> "#{@cfg.settings.clerkName} @ #{@cfg.settings.counterName}"
  initialMenuEnabled: true

  onFormSubmit: (input) ->
    Api.findItem(input, @)

  onResultSuccess: (data) ->
    row = @createRow("?", data.code, data.name, data.price)
    @cfg.uiRef.receiptResult.append(row)

  onResultError: (jqXHR) ->
    if jqXHR.status == 404
      alert("No such item")
      return
    return true

@ModeSwitcher.registerEntryPoint("reports", ItemFindMode)
