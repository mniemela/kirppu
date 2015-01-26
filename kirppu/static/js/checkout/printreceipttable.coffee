class @PrintReceiptTable extends ResultTable
  @strCode: "code"
  @strItem: "item"
  @strPrice: "price"
  @strVendor: "vendor"

  constructor: (args...)->
    super(args...)
    @head.append([
      "<th class=\"receipt_vendor_id\">#{ @constructor.strVendor }</th>"
      "<th class=\"receipt_code\">#{ @constructor.strCode }</th>"
      "<th class=\"receipt_item\">#{ @constructor.strItem }</th>"
      "<th class=\"receipt_price\">#{ @constructor.strPrice }</th>"
    ].map($))

  @joinedLine: (text="", html=false) ->
    $("<tr>").append($('<td colspan="4">')[if html then "html" else "text"](text))

  @createRow: (args..., price, rounded) ->
    row = $("<tr>")
    for x in [args..., displayPrice(price, rounded)]
      row.append($("<td>").text(x))
    return row
