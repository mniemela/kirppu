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


# Expose the localization instance in case we want to modify it.
window.localization = L
window.itemsConfig = C
window.toggleDelete = toggleDelete
