class @ItemCheckInMode extends ItemCheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_check_in", @)

  title: -> "Vendor Check-In"
  subtitle: -> "#{@cfg.settings.clerkName} @ #{@cfg.settings.counterName}"

  actions: -> [[
    '', (code) =>
      Api.item_checkin(
        code: code
      ).then(@onResultSuccess, @onResultError)
  ]]

  onResultSuccess: (data) =>
    row = @createRow("", data.code, data.name, data.price)
    @cfg.uiRef.receiptResult.prepend(row)

  onResultError: (jqXHR) =>
    if jqXHR.status == 404
      alert("No such item")
      return
    return true
