class @ItemFindMode extends ItemCheckoutMode
  ModeSwitcher.registerEntryPoint("reports", @)

  title: -> "Find"

  actions: -> [[
    '', (code) =>
      Api.item_find(
        code: code
      ).then(@onResultSuccess, @onResultError)
  ]]

  onResultSuccess: (data) =>
    row = @createRow("?", data.code, data.name, data.price)
    @receipt.body.append(row)

  onResultError: (jqXHR) =>
    if jqXHR.status == 404
      alert("No such item")
      return
    return true
