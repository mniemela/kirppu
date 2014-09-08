class @VendorCompensation extends CheckoutMode

  constructor: (cfg, switcher, vendor) ->
    super(cfg, switcher)
    @vendor = vendor

  title: -> "Vendor Compensation"

  enter: ->
    super
    @cfg.uiRef.body.append(new VendorInfo(@vendor).render())

    @abortButton = $('<input type="button">')
      .addClass('btn btn-default')
      .attr('value', 'Cancel')
      .click(@onCancel)
    @confirmButton = $('<input type="button">')
      .addClass('btn btn-success')
      .attr('value', 'Confirm')
      .prop('disabled', true)
      .click(@onConfirm)
    @cfg.uiRef.body.append(
      $('<form class="hidden-print">')
        .append(@confirmButton, @abortButton)
    )

    @itemDiv = $('<div>')
    @cfg.uiRef.body.append(@itemDiv)

    Api.item_list(vendor: @vendor.id).done(@onGotItems)

  onGotItems: (items) =>
    @compensableItems = (i for i in items when i.state == 'SO')

    if @compensableItems.length > 0
      table = new ItemReportTable('Sold Items')
      table.update(@compensableItems)
      @itemDiv.empty().append(table.render())
      @confirmButton.prop('disabled', false)

    else
      @itemDiv.empty().append($('<em>').text('No compensable items'))
      @confirmButton.prop('disabled', true)

  onCancel: => @switcher.switchTo(VendorReport, @vendor)

  onConfirm: =>
    @confirmButton.prop('disabled', true)
    nItems = @compensableItems.length
    for i in @compensableItems
      Api.item_compensate(code: i.code).done(=>
        nItems -= 1
        if nItems <= 0 then @onCompensated()
      )

  onCompensated: ->
    items = @compensableItems
    @compensableItems = []
    for i in items
      i.state = 'CO'
    table = new ItemReportTable('Compensated Items')
    table.update(items)
    @itemDiv.empty().append(table.render())
