tables = [
  ['Compensable Items', {SO: 0}]
  ['Returnable Items',  {BR: 0, ST: 0}]
  ['Other Items',       {MI: 0, RE: 0, CO: 0, AD: 0}]
]

class @VendorReport extends CheckoutMode
  constructor: (cfg, switcher, vendor) ->
    super(cfg, switcher)
    @vendor = vendor

  title: -> "Item Report"

  actions: -> [[
    "", (query) => @switcher.switchTo(VendorFindMode, query)
  ]]

  enter: ->
    super
    @cfg.uiRef.body.append(new VendorInfo(@vendor).render())
    compensateButton = $('<input type="button">')
      .addClass('btn btn-primary')
      .attr('value', 'Compensate')
      .click(@onCompensate)
    checkoutButton = $('<input type="button">')
      .addClass('btn btn-primary')
      .attr('value', 'Return Items')
      .click(@onReturn)
    @cfg.uiRef.body.append(
      $('<form class="hidden-print">').append(
        compensateButton,
        checkoutButton,
      )
    )

    Api.item_list(
      vendor: @vendor.id
    ).done(@onGotItems)

  onGotItems: (items) =>
    for [name, states] in tables
      matchingItems = (i for i in items when states[i.state]?)
      if matchingItems.length > 0
        table = new ItemReportTable(name)
        table.update(matchingItems)
        @cfg.uiRef.body.append(table.render())

  onCompensate: => @switcher.switchTo(VendorCompensation, @vendor)
  onReturn: =>     @switcher.switchTo(VendorCheckoutMode, @vendor)
