# All localizable strings for this file for now, until we have something
# better.
class LocalizationStrings
  toggleDelete:
    enabledText: 'Disable delete'
    disabledText: 'Enable delete'
  deleteItem:
    enabledTitle: 'Delete this item.'
    disabledTitle: 'Enable delete by clicking the button at the top of the page.'

L = new LocalizationStrings()  # Local shorthand for localization.


class PriceTagsConfig
  url_args:
    # This is used to move urls with arguments from django to JS.
    # It has to satisfy the regexp of the url in django.
    code: ''

  urls:
    roller: ''
    name_update: ''
    price_update: ''
    item_delete: ''
    size_update: ''

  constructor: ->

  name_update_url: (code) ->
    url = @urls.name_update
    return url.replace(@url_args.code, code)

  price_update_url: (code) ->
    url = @urls.price_update
    return url.replace(@url_args.code, code)

  item_delete_url: (code) ->
    url = @urls.item_delete
    return url.replace(@url_args.code, code)

  size_update_url: (code) ->
    url = @urls.size_update
    return url.replace(@url_args.code, code)

C = new PriceTagsConfig




# Whether delete buttons are in disabled state or not.
deleteIsDisabled = false

# Toggle between enabled and disabled states for all item delete buttons..
toggleDelete = ->
  # Toggle global state for all buttons between enabled and disabled.
  deleteIsDisabled = if deleteIsDisabled then false else true

  # Toggle the style of the toggle button it self.
  toggleButton = $('#toggle_delete')
  if deleteIsDisabled
    toggleButton.removeClass('btn-primary')
    toggleButton.addClass('btw-default')
    toggleButton.text(L.toggleDelete.disabledText)
  else
    toggleButton.removeClass('btw-default')
    toggleButton.addClass('btn-primary')
    toggleButton.text(L.toggleDelete.enabledText)

  # Toggle the item delete buttons between enabled/disabled.
  # These items also include the hidden template element, so there is
  # no need to handle that separately.
  deleteButtons = $('.item_button_delete')
  if deleteIsDisabled
    deleteButtons.attr('disabled', 'disabled')
    deleteButtons.attr('title', L.deleteItem.disabledTitle)
  else
    deleteButtons.removeAttr('disabled')
    deleteButtons.attr('title', L.deleteItem.enabledTitle)

  return


# Bind events for item price editing.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindPriceEditEvents = (tag, code) ->
  $(".item_price", tag).editable(
    C.price_update_url(code),
    indicator: "<img src='" + C.urls.roller + "'>"
    tooltip:   "Click to edit..."
    onblur:    "submit"
    style:     "width: 2cm"
    # Update the extra price display for long tags.
    callback:  (value, settings) -> $(".item_head_price", tag).text(value)
  )
  return


# Bind events for item name editing.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindNameEditEvents = (tag, code) ->
  $(".item_name", tag).editable(
    C.name_update_url(code),
    indicator: "<img src='" + C.urls.roller + "'>"
    tooltip:   "Click to edit..."
    onblur:    "submit"
    style:     "inherit"
  )
  return


# Bind events for item delete button.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindItemDeleteEvents = (tag, code) ->
  onItemDelete = ->
    $(tag).hide()
    $.ajax(
      url:  C.item_delete_url(code)
      type: 'DELETE'
      complete: (jqXHR, textStatus) ->
        if textStatus == "success" then tag.remove() else $(tag).show()
    )
    return

  $('.item_button_delete', tag).click(onItemDelete)
  return


# Bind events for item size toggle button.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindItemToggleEvents = (tag, code) ->
  onItemSizeToggle = ->
    tag_type = if $(tag).hasClass('item_short') then "long" else "short"
    $(tag).toggleClass('item_short')
    $.ajax(
      url:  C.size_update_url(code)
      type: 'POST'
      data:
        tag_type: tag_type
      complete: (jqXHR, textStatus) ->
        if textStatus != "success" then $(tag).toggleClass('item_short')
    )
    return

  $('.item_button_toggle', tag).click(onItemSizeToggle)
  return


# Bind all events for '.item_container' element.
# @note Target for jQuery.each.
# @param index [Number] Index from jQuery.each, not used.
# @param tag [jQuery element] An '.item_container' element.
bindOneTagsEvents = (index, tag) ->
  code = $(".item_extra_code", tag).text()

  bindPriceEditEvents(tag, code)
  bindNameEditEvents(tag, code)
  bindItemDeleteEvents(tag, code)
  bindItemToggleEvents(tag, code)

  return


# Bind events for a set of '.item_container' elements.
# @param tags [jQuery set] A set of '.item_container' elements.
bindTagEvents = (tags) ->
  tags.each(bindOneTagsEvents)

  return


# Expose the localization instance in case we want to modify it.
window.localization = L
window.itemsConfig = C
window.toggleDelete = toggleDelete
window.bindTagEvents = bindTagEvents
