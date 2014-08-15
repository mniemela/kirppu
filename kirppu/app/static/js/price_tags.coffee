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
window.toggleDelete = toggleDelete
