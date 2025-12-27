# Tasks: authenticate-with-key

## 1. Add API Key Constant

- [ ] 1.1 Open `custom_components/jellyfin/const.py`
- [ ] 1.2 Add a new constant: `CONF_API_KEY = "api_key"`
- [ ] 1.3 This constant will be used as the key in config entry data storage

## 2. Update Config Flow Schema

- [ ] 2.1 Open `custom_components/jellyfin/config_flow.py`
- [ ] 2.2 Remove imports for `CONF_USERNAME`, `CONF_PASSWORD`, `CONF_CLIENT_ID` from `homeassistant.const` (lines 13-15)
- [ ] 2.3 Add import for `CONF_API_KEY` from `.const`
- [ ] 2.4 In `async_step_user()` (line 61-68), replace the `data_schema` dict:
  - Remove: `vol.Required(CONF_USERNAME): str`
  - Remove: `vol.Optional(CONF_PASSWORD, default=""): str`
  - Add: `vol.Required(CONF_API_KEY): str`
- [ ] 2.5 Remove instance variables `self._username` and `self._password` from `__init__` if present
- [ ] 2.6 Update the `user_input` handling (lines 71-76):
  - Remove: `self._username = user_input[CONF_USERNAME]`
  - Remove: `self._password = user_input[CONF_PASSWORD]`
  - Add: `self._api_key = user_input[CONF_API_KEY]`

## 3. Update Config Entry Data Storage

- [ ] 3.1 In `async_step_user()`, update `async_create_entry()` data dict (lines 84-92):
  - Remove: `CONF_USERNAME: self._username`
  - Remove: `CONF_PASSWORD: self._password`
  - Remove: `CONF_CLIENT_ID: str(uuid.uuid4())`
  - Add: `CONF_API_KEY: self._api_key`
- [ ] 3.2 Remove the `import uuid` at the top of the file (line 4) - no longer needed

## 4. Update Options Flow

- [ ] 4.1 In `JellyfinOptionsFlowHandler.__init__()` (lines 117-125):
  - Remove: `self._username = ...` line
  - Remove: `self._password = ...` line
  - Add: `self._api_key = config_entry.data.get(CONF_API_KEY, "")`
- [ ] 4.2 In `async_step_user()` data_schema (lines 142-149):
  - Remove: `vol.Required(CONF_USERNAME, default=self._username): str`
  - Remove: `vol.Required(CONF_PASSWORD, default=self._password): str`
  - Add: `vol.Required(CONF_API_KEY, default=self._api_key): str`
- [ ] 4.3 Update user_input handling (lines 135-140):
  - Remove: `self._username = user_input[CONF_USERNAME]`
  - Remove: `self._password = user_input[CONF_PASSWORD]`
  - Add: `self._api_key = user_input[CONF_API_KEY]`
- [ ] 4.4 Update `async_create_entry()` data dict (lines 155-161):
  - Remove: `CONF_USERNAME: self._username`
  - Remove: `CONF_PASSWORD: self._password`
  - Add: `CONF_API_KEY: self._api_key`

## 5. Add Test Connection Button

- [ ] 5.1 Add a helper method to test the API key connection:
  ```python
  async def _test_connection(self, url: str, api_key: str, verify_ssl: bool) -> bool:
      """Test API key by connecting to server."""
      from jellyfin_apiclient_python import JellyfinClient
      from .const import USER_APP_NAME, CLIENT_VERSION

      try:
          client = JellyfinClient()
          client.config.data["app.name"] = USER_APP_NAME
          client.config.data["app.version"] = CLIENT_VERSION
          client.config.data["auth.ssl"] = verify_ssl

          # Normalize URL
          if url.endswith("/"):
              url = url[:-1]

          client.authenticate(
              {"Servers": [{"AccessToken": api_key, "address": url}]},
              discover=False
          )

          # Test by fetching system info
          info = client.jellyfin.get_system_info()
          return info is not None
      except Exception:
          return False
  ```
- [ ] 5.2 Add a new step for testing connection. In Home Assistant config flows, you can add a "test" action by creating a step that shows results:
  ```python
  async def async_step_test(self, user_input=None):
      """Handle connection test."""
      success = await self.hass.async_add_executor_job(
          self._test_connection_sync,
          self._url,
          self._api_key,
          self._verify_ssl
      )

      if success:
          return self.async_show_form(
              step_id="user",
              data_schema=...,
              description_placeholders={"test_result": "Connection successful!"}
          )
      else:
          return self.async_show_form(
              step_id="user",
              data_schema=...,
              errors={"base": "cannot_connect"}
          )
  ```
- [ ] 5.3 Research Home Assistant config flow patterns for "test connection" buttons - may need to use `async_show_progress` or a menu step

## 6. Update Client Factory

- [ ] 6.1 Open `custom_components/jellyfin/__init__.py`
- [ ] 6.2 Remove imports for `CONF_USERNAME`, `CONF_PASSWORD`, `CONF_CLIENT_ID` from `homeassistant.const`
- [ ] 6.3 Add import for `CONF_API_KEY` from `.const`
- [ ] 6.4 Modify `client_factory()` (lines 591-599) to not configure device identity:
  ```python
  @staticmethod
  def client_factory(verify_ssl: bool):
      client = JellyfinClient(allow_multiple_clients=True)
      client.config.data["app.default"] = True
      client.config.data["app.name"] = USER_APP_NAME
      client.config.data["app.version"] = CLIENT_VERSION
      client.config.data["auth.ssl"] = verify_ssl
      return client
  ```
  - Remove: `client.config.app(...)` call (this sets device name/id which we don't want)

## 7. Update Login Method

- [ ] 7.1 Modify `login()` method (lines 601-638) to use API key authentication:
  ```python
  def login(self):
      autolog(">>>")

      # URL normalization (keep existing logic from lines 604-625)
      self.server_url = self.config_entry[CONF_URL]
      if self.server_url.endswith("/"):
          self.server_url = self.server_url[:-1]
      # ... rest of URL normalization ...

      # Create client
      self.jf_client = self.client_factory(self.config_entry[CONF_VERIFY_SSL])

      # Authenticate with API key directly
      self.jf_client.authenticate(
          {"Servers": [{"AccessToken": self.config_entry[CONF_API_KEY], "address": self.server_url}]},
          discover=False
      )

      return True
  ```
- [ ] 7.2 Remove these lines from the current implementation:
  - `status = self.jf_client.auth.connect_to_address(self.server_url)` and its check
  - `result = self.jf_client.auth.login(...)` and its check
  - `credentials = self.jf_client.auth.credentials.get_credentials()`
  - `self.jf_client.authenticate(credentials)`

## 8. Update UI Strings

- [ ] 8.1 Open `custom_components/jellyfin/strings.json`
- [ ] 8.2 In `config.step.user.data`:
  - Remove: `"username": "..."` line
  - Remove: `"password": "..."` line
  - Add: `"api_key": "API Key"`
- [ ] 8.3 In `options.step.user.data`:
  - Remove: `"username": "..."` line
  - Remove: `"password": "..."` line
  - Add: `"api_key": "API Key"`
- [ ] 8.4 Add error string for test failure if needed: `"test_failed": "Connection test failed"`

## 9. Update Translations

- [ ] 9.1 Open `custom_components/jellyfin/translations/en.json` and make same changes as strings.json
- [ ] 9.2 Open `custom_components/jellyfin/translations/de.json` and update:
  - Remove username/password entries
  - Add: `"api_key": "API-Schlüssel"`
- [ ] 9.3 Open `custom_components/jellyfin/translations/fr.json` and update:
  - Remove username/password entries
  - Add: `"api_key": "Clé API"`

## 10. Validation

- [ ] 10.1 Remove the integration from Home Assistant if previously configured
- [ ] 10.2 Restart Home Assistant
- [ ] 10.3 Add the integration via UI - verify API key field appears
- [ ] 10.4 Test with a valid API key - verify connection succeeds
- [ ] 10.5 Test with an invalid API key - verify appropriate error shown
- [ ] 10.6 Test the "Test Connection" button works correctly
- [ ] 10.7 Verify media player entities appear after successful configuration
