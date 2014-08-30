# Base class for modes where the receipt is a list of items.
#
# @abstract
class @ItemCheckoutMode extends CheckoutMode

  columns: -> [
    '<th class="receipt_index">#</th>',
    '<th class="receipt_code">code</th>',
    '<th class="receipt_item">item</th>',
    '<th class="receipt_price">price</th>',
  ].map($)

  # Create a row in receipt table.
  # All arguments are used for display-only.
  #
  # @param index [Integer] Index of the item.
  # @param code [String] Item code.
  # @param name [String] Item name.
  # @param price [Integer, optional] Price of the item in cents.
  # @param rounded [Boolean, optional] Should the price be displayed also as rounded?
  # @return [$] Table row (tr element) as jQuery object.
  createRow: (index, code, name, price=null, rounded=false) ->
    if price?
      if Number.isInteger(price)
        price_str = price.formatCents() + "€"
      else
        price_str = price
        rounded = false
    else
      price_str = ""
      rounded = false

    if rounded
      rounded_str = price.round5().formatCents() + "€"
      price_str = "#{ rounded_str } (#{ price_str })"

    row = $("<tr>")
    row.append.apply(
      row,
      $("<td>").text(x) for x in [index, code, name, price_str]
    )

# Round the number to closest modulo 5.
#
# @return Integer rounded to closest 5.
Number.prototype.round5 = ->
  modulo = this % 5

  # 2.5 == split-point, i.e. half of 5.
  if modulo >= 2.5
    return this + (5 - modulo)
  else
    return this - modulo
