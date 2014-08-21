class @ClerkLoginMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("clerk_login", @)

  title: -> "Locked"
  subtitle: -> "Login..."

  enter: ->
    super
    @switcher.setMenuEnabled(false)

  actions: -> [[
    @cfg.settings.clerkPrefix,
    (code, prefix) =>
      Api.clerkLogin(prefix + code, @cfg.settings.counterCode, @)
  ]]

  onResultSuccess: (data) ->
    username = data["user"]
    @cfg.settings.clerkName = username
    console.log("Logged in as #{username}.")
    @switcher.switchTo(CounterMode)

  onResultError: (jqXHR) ->
    if jqXHR.status == 419
      console.log("Login failed: " + jqXHR.responseJSON["message"])
      return
    return true
