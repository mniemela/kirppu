class @ItemCheckInMode extends ItemCheckoutMode

  title: -> "Vendor Check-In"
  subtitle: -> "#{@cfg.settings.clerkName} @ #{@cfg.settings.counterName}"
  initialMenuEnabled: true

  onFormSubmit: (input) ->
    Api.checkInItem(input, @)

  onResultSuccess: (data) ->
    row = @createRow("", data.code, data.name, data.price)
    @cfg.uiRef.receiptResult.prepend(row)

  onResultError: (jqXHR) ->
    if jqXHR.status == 404
      alert("No such item")
      return
    return true

@ModeSwitcher.registerEntryPoint("vendor_check_in", ItemCheckInMode)
