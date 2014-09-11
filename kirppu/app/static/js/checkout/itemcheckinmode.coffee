class @ItemCheckInMode extends ItemCheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_check_in", @)

  glyph: -> "import"
  title: -> "Vendor Check-In"

  actions: -> [[
    '', (code) =>
      Api.item_checkin(
        code: code
      ).then(@onResultSuccess, @onResultError)
  ]]

  onResultSuccess: (data) =>
    row = @createRow("", data.code, data.name, data.price)
    @receipt.body.prepend(row)

  onResultError: (jqXHR) =>
    if jqXHR.status == 404
      alert("No such item")
      return
    return true
