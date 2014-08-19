class @ClerkLoginMode extends CheckoutMode
  constructor: (config) ->
    super(config)
    @_prefix = @cfg.settings.clerkPrefix

  title: -> "Locked"
  subtitle: -> "Login..."
  initialMenuEnabled: false

  onFormSubmit: (input) ->
    if input.indexOf(@_prefix) != 0
      return false
    Api.clerkLogin(input, @cfg.settings.counterCode, @)

  onResultSuccess: (data) ->
    username = data["user"]
    @cfg.settings.clerkName = username
    console.log("Logged in as #{username}.")
    @switchTo(CounterMode)

  onResultError: (jqXHR) ->
    if jqXHR.status == 419
      console.log("Login failed: " + jqXHR.responseJSON["message"])
      return
    return true

@ModeSwitcher.registerEntryPoint("clerk_login", ClerkLoginMode)
