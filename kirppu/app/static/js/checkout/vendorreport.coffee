# Create a new class for the report mode of the vendor.
@vendorReport = (vendor) ->
  class VendorReport extends ItemCheckoutMode

    title: -> "Item Report"

    enter: ->
      super
      Api.item_list(
        vendor: vendor.id
      ).done(@onGotItems)

    onGotItems: (items) =>
      console.log(items)
      for item, index in items
        @receipt.body.append(
          @createRow(index, item.code, item.name, item.price)
        )
