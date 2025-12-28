"""Config flow for Jellyfin."""
import asyncio
import logging

import voluptuous as vol

from jellyfin_apiclient_python import JellyfinClient
from homeassistant import config_entries, exceptions
from homeassistant.core import callback
from homeassistant.const import ( # pylint: disable=import-error
    CONF_URL,
    CONF_VERIFY_SSL,
)

from .const import (
    CLIENT_VERSION,
    CONF_API_KEY,
    DOMAIN,
    DEFAULT_SSL,
    DEFAULT_VERIFY_SSL,
    CONF_GENERATE_UPCOMING,
    CONF_GENERATE_YAMC,
    USER_APP_NAME,
)
from .url import normalize_server_url
_LOGGER = logging.getLogger(__name__)

RESULT_CONN_ERROR = "cannot_connect"
RESULT_LOG_MESSAGE = {RESULT_CONN_ERROR: "Connection error"}


@config_entries.HANDLERS.register(DOMAIN)
class JellyfinFlowHandler(config_entries.ConfigFlow):
    """Config flow for Jellyfin component."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Jellyfin options callback."""
        return JellyfinOptionsFlowHandler(config_entry)

    def __init__(self):
        """Init JellyfinFlowHandler."""
        self._errors = {}
        self._url = None
        self._api_key = None
        self._ssl = DEFAULT_SSL
        self._verify_ssl = DEFAULT_VERIFY_SSL
        self._is_import = False

    @staticmethod
    def _test_connection(url: str, api_key: str, verify_ssl: bool) -> bool:
        """Test API key by connecting to the server."""
        try:
            client = JellyfinClient(allow_multiple_clients=True)
            client.config.data["app.default"] = True
            client.config.data["app.name"] = USER_APP_NAME
            client.config.data["app.version"] = CLIENT_VERSION
            client.config.data["auth.ssl"] = verify_ssl

            server_url = normalize_server_url(url)
            client.authenticate(
                {"Servers": [{"AccessToken": api_key, "address": server_url}]},
                discover=False,
            )
            info = client.jellyfin.get_system_info()
            return info is not None
        except Exception:
            _LOGGER.debug("API key validation failed.", exc_info=True)
            return False

    async def async_step_import(self, user_input=None):
        """Handle configuration by yaml file."""
        self._is_import = True
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""

        self._errors = {}

        data_schema = {
            vol.Required(CONF_URL): str,
            vol.Required(CONF_API_KEY): str,
            vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
            vol.Optional(CONF_GENERATE_UPCOMING, default=False): bool,
            vol.Optional(CONF_GENERATE_YAMC, default=False): bool,
        }

        if user_input is not None:
            self._url = str(user_input[CONF_URL])
            self._api_key = user_input[CONF_API_KEY]
            self._verify_ssl = user_input[CONF_VERIFY_SSL]
            self._generate_upcoming = user_input[CONF_GENERATE_UPCOMING]
            self._generate_yamc = user_input[CONF_GENERATE_YAMC]

            try:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                is_valid = await self.hass.async_add_executor_job(
                    self._test_connection,
                    self._url,
                    self._api_key,
                    self._verify_ssl,
                )
                if not is_valid:
                    raise CannotConnect

                return self.async_create_entry(
                    title=DOMAIN,
                    data={
                        CONF_URL: self._url,
                        CONF_API_KEY: self._api_key,
                        CONF_VERIFY_SSL: self._verify_ssl,
                        CONF_GENERATE_UPCOMING: self._generate_upcoming,
                        CONF_GENERATE_YAMC: self._generate_yamc,
                    },
                )

            except (asyncio.TimeoutError, CannotConnect):
                result = RESULT_CONN_ERROR

            if self._is_import:
                _LOGGER.error(
                    "Error importing from configuration.yaml: %s",
                    RESULT_LOG_MESSAGE.get(result, "Generic Error"),
                )
                return self.async_abort(reason=result)

            self._errors["base"] = result

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )


class JellyfinOptionsFlowHandler(config_entries.OptionsFlow):
    """Option flow for Jellyfin component."""

    def __init__(self, config_entry):
        """Init JellyfinOptionsFlowHandler."""
        self._errors = {}
        self._url = config_entry.data[CONF_URL] if CONF_URL in config_entry.data else None
        self._api_key = config_entry.data.get(CONF_API_KEY, "")
        self._verify_ssl = config_entry.data[CONF_VERIFY_SSL] if CONF_VERIFY_SSL in config_entry.data else DEFAULT_VERIFY_SSL
        self._generate_upcoming = config_entry.data[CONF_GENERATE_UPCOMING] if CONF_GENERATE_UPCOMING in config_entry.data else False
        self._generate_yamc = config_entry.data[CONF_GENERATE_YAMC] if CONF_GENERATE_YAMC in config_entry.data else False

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        self._errors = {}

        if user_input is not None:
            self._url = str(user_input[CONF_URL])
            self._api_key = user_input[CONF_API_KEY]
            self._verify_ssl = user_input[CONF_VERIFY_SSL]
            self._generate_upcoming = user_input[CONF_GENERATE_UPCOMING]
            self._generate_yamc = user_input[CONF_GENERATE_YAMC]

        data_schema = {
            vol.Required(CONF_URL, default=self._url): str,
            vol.Required(CONF_API_KEY, default=self._api_key): str,
            vol.Optional(CONF_VERIFY_SSL, default=self._verify_ssl): bool,
            vol.Optional(CONF_GENERATE_UPCOMING, default=self._generate_upcoming): bool,
            vol.Optional(CONF_GENERATE_YAMC, default=self._generate_yamc): bool,
        }

        if user_input is not None:
            try:
                return self.async_create_entry(
                    title=DOMAIN,
                    data={
                        CONF_URL: self._url,
                        CONF_API_KEY: self._api_key,
                        CONF_VERIFY_SSL: self._verify_ssl,
                        CONF_GENERATE_UPCOMING: self._generate_upcoming,
                        CONF_GENERATE_YAMC: self._generate_yamc,
                    },
                )

            except (asyncio.TimeoutError, CannotConnect):
                _LOGGER.error("cannot connect")
                result = RESULT_CONN_ERROR

            self._errors["base"] = result

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we can not connect."""
