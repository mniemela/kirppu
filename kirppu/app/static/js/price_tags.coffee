
class PriceTagsConfig
  url_args:
    # This is used to move urls with arguments from django to JS.
    # It has to satisfy the regexp of the url in django.
    code: ''

  urls:
    roller: ''
    name_update: ''
    price_update: ''
    item_to_list: ''
    size_update: ''
    item_add: ''
    barcode_img: ''
    item_to_print: ''
    all_to_print: ''

  constructor: ->

  name_update_url: (code) ->
    url = @urls.name_update
    return url.replace(@url_args.code, code)

  price_update_url: (code) ->
    url = @urls.price_update
    return url.replace(@url_args.code, code)

  item_to_list_url: (code) ->
    url = @urls.item_to_list
    return url.replace(@url_args.code, code)

  size_update_url: (code) ->
    url = @urls.size_update
    return url.replace(@url_args.code, code)

  barcode_img_url: (code) ->
    url = @urls.barcode_img
    return url.replace(@url_args.code, code)

  item_to_print_url: (code) ->
    url = @urls.item_to_print
    return url.replace(@url_args.code, code)

C = new PriceTagsConfig


createTag = (name, price, vendor_id, code, type) ->
  # Find the hidden template element, clone it and replace the contents.
  tag = $(".item_template").clone();
  tag.removeClass("item_template");

  if (type == "short") then tag.addClass("item_short")
  if (type == "tiny") then tag.addClass("item_tiny")

  $('.item_name', tag).text(name)
  $('.item_price', tag).text(price)
  $('.item_head_price', tag).text(price)
  $('.item_vendor_id', tag).text(vendor_id)
  $(tag).attr('id', code)
  $('.item_extra_code', tag).text(code)

  $('.barcode_container > img', tag).attr('src', C.barcode_img_url(code))

  return tag


# Add an item with name and price set to form contents.
addItem = ->
  onSuccess = (items) ->
    for item in items
      tag = createTag(item.name, item.price, item.vendor_id, item.code, item.type)
      $('#items').prepend(tag)
      bindTagEvents($(tag))

  content =
    name: $("#item-add-name").val()
    price: $("#item-add-price").val()
    range: $("#item-add-suffixes").val()
    type: $("input[name=item-add-type]:checked").val()

  $.post(C.urls.item_add, content, onSuccess)


deleteAll = ->
  if not confirm(gettext('This will mark all items as printed so they can no longer be edited. Continue?'))
    return

  tags = $('#items > .item_container')
  $(tags).hide('slow')

  $.ajax(
    url:  C.urls.all_to_print
    type: 'POST'
    success: ->
      $(tags).each((index, tag) ->
        code = $(tag).attr('id')
        moveItemToList(tag, code)
      )
    error: ->
      $(tags).show('slow')
  )

  return


# Whether delete buttons are in disabled state or not.
deleteIsDisabled = false

# Toggle between enabled and disabled states for all item delete buttons..
toggleDelete = ->
  # Toggle global state for all buttons between enabled and disabled.
  deleteIsDisabled = if deleteIsDisabled then false else true

  # Toggle the style of the toggle button it self.
  toggleButton = $('#toggle_delete')
  if deleteIsDisabled
    toggleButton.removeClass('active')
    toggleButton.addClass('btw-default')
  else
    toggleButton.removeClass('btw-default')
    toggleButton.addClass('active')

  # Toggle the item delete buttons between enabled/disabled.
  # These items also include the hidden template element, so there is
  # no need to handle that separately.
  deleteButtons = $('.item_button_delete')
  if deleteIsDisabled
    deleteButtons.attr('disabled', 'disabled')
    deleteButtons.attr('title', gettext('Mark this item as printed. Enable this button from the top of the page.'))
  else
    deleteButtons.removeAttr('disabled')
    deleteButtons.attr('title', gettext('Mark this item as printed.'))

  return


listViewIsOn = false;

toggleListView = ->
  listViewIsOn = if listViewIsOn then false else true

  items = $('#items > .item_container')
  if listViewIsOn
    items.addClass('item_list')
  else
    items.removeClass('item_list')


onPriceChange = ->
  input = $(this)
  formGroup = input.parents(".form-group")

  # Replace ',' with '.' in order to accept numbers with ',' as the period.
  value = input.val().replace(',', '.')
  if value > 400 or value <= 0 or Number.isNaN(Number.parseInt(value))
    formGroup.addClass('has-error')
  else
    formGroup.removeClass('has-error')

  return


bindFormEvents = ->
  $('#add_short_item').click(addItem);
  $('#delete_all').click(deleteAll);
  $('#toggle_delete').click(toggleDelete);
  $('#list_view').click(toggleListView)
  toggleDelete(); # Initialize delete buttons to disabled.

  $('#item-add-price').change(onPriceChange);

  return


# Bind events for item price editing.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindPriceEditEvents = (tag, code) ->
  $(".item_price", tag).editable(
    C.price_update_url(code),
    indicator: "<img src='" + C.urls.roller + "'>"
    tooltip:   gettext("Click to edit...")
    placeholder: gettext("Click to edit")
    onblur:    "submit"
    style:     "width: 2cm"
    # Update the extra price display for long tags.
    callback:  (value) -> $(".item_head_price", tag).text(value)
  )
  return


# Bind events for item name editing.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindNameEditEvents = (tag, code) ->
  $(".item_name", tag).editable(
    C.name_update_url(code),
    indicator: "<img src='" + C.urls.roller + "'>"
    tooltip:   gettext("Click to edit...")
    placeholder: gettext("Click to edit")
    onblur:    "submit"
    style:     "inherit"
  )
  return


moveToPrint = (tag, code) ->
  $.ajax(
    url: C.item_to_print_url(code)
    type: 'POST'

    success: (item) ->
      $(tag).remove()

      new_tag = createTag(item.name, item.price, item.vendor_id, item.code, item.type)
      $(new_tag).hide()
      $(new_tag).appendTo("#items")
      $(new_tag).show('slow')
      bindTagEvents($(new_tag))

    error: (item) ->
      $(tag).show('slow')
  )
  return


moveItemToList = (tag, code) ->
  unbindTagEvents($(tag))

  $('.item_button_delete', tag).click(-> onClickToPrint(tag, code))
  $(tag).prependTo("#printed_items")
  $(tag).addClass("item_list")
  $(tag).show('slow')


moveToList = (tag, code) ->
  $.ajax(
    url:  C.item_to_list_url(code)
    type: 'POST'

    success: ->
      moveItemToList(tag, code)

    error: ->
      $(tag).show('slow')
  )
  return


onClickToList = (tag, code) ->
  $(tag).hide('slow', -> moveToList(tag, code))


onClickToPrint = (tag, code) ->
  $(tag).hide('slow', -> moveToPrint(tag, code))


# Bind events for item delete button.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindItemToListEvents = (tag, code) ->
  $('.item_button_delete', tag).click(-> onClickToList(tag, code))
  return


# Bind events for item delete button.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindItemToPrintEvents = (tag, code) ->
  $('.item_button_delete', tag).click(-> onClickToPrint(tag, code))
  return


# Bind events for item size toggle button.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindItemToggleEvents = (tag, code) ->
  setTagType = (tag_type) ->
    if tag_type == "tiny"
      $(tag).addClass('item_tiny')
    else
      $(tag).removeClass('item_tiny')
    if tag_type == "short"
      $(tag).addClass('item_short')
    else
      $(tag).removeClass('item_short')
    return

  getNextType = (tag_type) ->
    tag_type = switch tag_type
      when "tiny" then "short"
      when "short" then "long"
      when "long" then "tiny"
      else "short"
    return tag_type

  onItemSizeToggle = ->
    if $(tag).hasClass('item_short')
      tag_type = "short"
    else if $(tag).hasClass('item_tiny')
      tag_type = "tiny"
    else
      tag_type = "long"

    # Apply next type immediately and backtrack if the ajax call fails.
    new_tag_type = getNextType(tag_type)
    setTagType(new_tag_type)

    $.ajax(
      url:  C.size_update_url(code)
      type: 'POST'
      data:
        tag_type: new_tag_type
      complete: (jqXHR, textStatus) ->
        if textStatus != "success" then setTagType(tag_type)
    )

    return

  $('.item_button_toggle', tag).click(onItemSizeToggle)
  return


# Bind events for a set of '.item_container' elements.
# @param tags [jQuery set] A set of '.item_container' elements.
bindTagEvents = (tags) ->
  tags.each((index, tag) ->
    code = $(tag).attr('id')

    bindPriceEditEvents(tag, code)
    bindNameEditEvents(tag, code)
    bindItemToListEvents(tag, code)
    bindItemToggleEvents(tag, code)

    return
  )
  return


bindListTagEvents = (tags) ->
  tags.each((index, tag) ->
    code = $(tag).attr('id')

    bindItemToPrintEvents(tag, code)

    return
  )
  return


# Unbind events bound by bindTagEvents and bindListTagEvents.
unbindTagEvents = (tags) ->
  tags.each((index, tag) ->

    $('.item_name', tag).unbind('click')
    $('.item_price', tag).unbind('click')
    $('.item_button_toggle', tag).unbind('click')
    $('.item_button_delete', tag).unbind('click')

    return
  )
  return



window.itemsConfig = C
window.addItem = addItem
window.deleteAll = deleteAll
window.toggleDelete = toggleDelete
window.bindTagEvents = bindTagEvents
window.bindListTagEvents = bindListTagEvents
window.bindFormEvents = bindFormEvents
