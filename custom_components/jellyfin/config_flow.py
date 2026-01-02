"""Config flow for Jellyfin."""
import asyncio
import logging
from typing import Any

import voluptuous as vol

from jellyfin_apiclient_python import JellyfinClient
from homeassistant import config_entries, exceptions
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback
from homeassistant.const import (  # pylint: disable=import-error
    CONF_URL,
    CONF_VERIFY_SSL,
)
from homeassistant.helpers.selector import selector

from .const import (
    CLIENT_VERSION,
    CONF_API_KEY,
    CONF_GENERATE_UPCOMING,
    CONF_GENERATE_YAMC,
    CONF_LIBRARY_USER_ID,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    USER_APP_NAME,
)
from .models import JellyfinEntryData
from .url import normalize_server_url

_LOGGER = logging.getLogger(__name__)

RESULT_CONN_ERROR = "cannot_connect"
RESULT_LOG_MESSAGE = {RESULT_CONN_ERROR: "Connection error"}
ERROR_USER_REQUIRED = "user_required"
ERROR_USER_FETCH = "user_fetch_failed"


class UserSelectionError(exceptions.HomeAssistantError):
    """Raised when Jellyfin users cannot be loaded."""


class JellyfinFlowBase:
    """Shared helpers for config and options flows."""

    def __init__(self):
        super().__init__()
        self._client: JellyfinClient | None = None
        self._pending_entry_data: JellyfinEntryData | None = None
        self._library_user_id: str | None = None

    def _client_factory(self, verify_ssl: bool) -> JellyfinClient:
        client = JellyfinClient(allow_multiple_clients=True)
        client.config.data["app.default"] = True
        client.config.data["app.name"] = USER_APP_NAME
        client.config.data["app.version"] = CLIENT_VERSION
        client.config.data["auth.ssl"] = verify_ssl
        return client

    def _authenticate_client(self, url: str, api_key: str, verify_ssl: bool) -> JellyfinClient:
        client = self._client_factory(verify_ssl)
        try:
            server_url = normalize_server_url(url)
        except ValueError as err:
            raise CannotConnect from err

        try:
            client.authenticate(
                {"Servers": [{"AccessToken": api_key, "address": server_url}]},
                discover=False,
            )
            info = client.jellyfin.get_system_info()
        except Exception as exc:
            _LOGGER.debug("API key validation failed.", exc_info=True)
            raise CannotConnect from exc

        if info is None:
            raise CannotConnect

        return client

    def _format_user_label(self, user: dict[str, Any]) -> str | None:
        user_id = user.get("Id")
        if not user_id:
            return None
        name = user.get("Name") or user.get("Username")
        username = user.get("Username")
        if name and username and name != username:
            return f"{name} ({username})"
        return name or user_id

    def _fetch_user_options_from_client(self, client: JellyfinClient) -> list[dict[str, str]]:
        if client is None:
            raise UserSelectionError
        try:
            users = client.jellyfin.get_public_users()
            if not users:
                users = client.jellyfin.get_users()
        except Exception as exc:
            _LOGGER.debug("Failed to fetch Jellyfin users.", exc_info=True)
            raise UserSelectionError from exc

        options: list[dict[str, str]] = []
        for user in users or []:
            label = self._format_user_label(user)
            if not label:
                continue
            options.append({"label": label, "value": user["Id"]})

        if not options:
            raise UserSelectionError
        return options

    async def _async_get_user_options(self) -> list[dict[str, str]]:
        return await self.hass.async_add_executor_job(
            self._fetch_user_options_from_client,
            self._client,
        )

    def _build_user_schema(self, default_value: str | None, options: list[dict[str, str]]) -> vol.Schema:
        select = selector(
            {
                "select": {
                    "options": options,
                    "mode": "dropdown",
                }
            }
        )
        default = default_value if default_value is not None else vol.UNDEFINED
        return vol.Schema(
            {
                vol.Required(
                    CONF_LIBRARY_USER_ID,
                    default=default,
                ): select
            }
        )

    def _create_entry_from_pending(self, title: str) -> ConfigFlowResult:
        if self._pending_entry_data is None:
            raise ValueError("No pending entry data")
        data = self._pending_entry_data.model_dump()
        self._pending_entry_data = None
        self._client = None
        return self.async_create_entry(title=title, data=data)  # type: ignore[return-value]


@config_entries.HANDLERS.register(DOMAIN)
class JellyfinFlowHandler(JellyfinFlowBase, config_entries.ConfigFlow):
    """Config flow for Jellyfin component."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "JellyfinOptionsFlowHandler":
        """Jellyfin options callback."""
        return JellyfinOptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        super().__init__()
        self._errors: dict[str, str] = {}
        self._url: str | None = None
        self._api_key: str | None = None
        self._verify_ssl = DEFAULT_VERIFY_SSL
        self._generate_upcoming = False
        self._generate_yamc = False
        self._is_import = False

    async def async_step_import(self, user_input: dict[str, object] | None = None) -> ConfigFlowResult:
        """Handle configuration by yaml file."""
        self._is_import = True
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input: dict[str, object] | None = None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            self._url = str(user_input[CONF_URL])
            self._api_key = user_input[CONF_API_KEY]
            self._verify_ssl = user_input[CONF_VERIFY_SSL]
            self._generate_upcoming = user_input[CONF_GENERATE_UPCOMING]
            self._generate_yamc = user_input[CONF_GENERATE_YAMC]
            needs_user = self._generate_upcoming or self._generate_yamc

            try:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                self._client = await self.hass.async_add_executor_job(
                    self._authenticate_client,
                    self._url,
                    self._api_key,
                    self._verify_ssl,
                )

                # Build pending entry data - validation deferred if needs_user
                self._pending_entry_data = JellyfinEntryData.model_construct(
                    url=self._url,
                    api_key=self._api_key,
                    verify_ssl=self._verify_ssl,
                    generate_upcoming=self._generate_upcoming,
                    generate_yamc=self._generate_yamc,
                    library_user_id=None,
                )

                if needs_user:
                    self._library_user_id = None
                    return await self.async_step_select_user()

                return self._create_entry_from_pending(self._url)

            except (asyncio.TimeoutError, CannotConnect):
                result = RESULT_CONN_ERROR

            if self._is_import:
                _LOGGER.error(
                    "Error importing from configuration.yaml: %s",
                    RESULT_LOG_MESSAGE.get(result, "Generic Error"),
                )
                return self.async_abort(reason=result)

            self._errors["base"] = result

        data_schema = {
            vol.Required(CONF_URL, default=self._url or ""): str,
            vol.Required(CONF_API_KEY, default=self._api_key or ""): str,
            vol.Optional(CONF_VERIFY_SSL, default=self._verify_ssl): bool,
            vol.Optional(CONF_GENERATE_UPCOMING, default=self._generate_upcoming): bool,
            vol.Optional(CONF_GENERATE_YAMC, default=self._generate_yamc): bool,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )

    async def async_step_select_user(self, user_input: dict[str, object] | None = None) -> ConfigFlowResult:
        """Select the Jellyfin user for optional features."""
        self._errors = {}

        if user_input is not None:
            raw_library_user_id = user_input.get(CONF_LIBRARY_USER_ID)
            if not raw_library_user_id:
                self._errors["base"] = ERROR_USER_REQUIRED
            elif self._pending_entry_data is None:
                raise ValueError("No pending entry data")
            else:
                library_user_id = str(raw_library_user_id)
                # Rebuild with user and validate
                self._pending_entry_data = JellyfinEntryData(
                    url=self._pending_entry_data.url,
                    api_key=self._pending_entry_data.api_key,
                    verify_ssl=self._pending_entry_data.verify_ssl,
                    generate_upcoming=self._pending_entry_data.generate_upcoming,
                    generate_yamc=self._pending_entry_data.generate_yamc,
                    library_user_id=library_user_id,
                )
                self._library_user_id = library_user_id
                return self._create_entry_from_pending(self._url)

        try:
            user_options = await self._async_get_user_options()
        except UserSelectionError:
            self._errors["base"] = ERROR_USER_FETCH
            user_options = []

        if not user_options:
            return self.async_show_form(
                step_id="select_user",
                data_schema=vol.Schema({}),
                errors=self._errors,
            )

        return self.async_show_form(
            step_id="select_user",
            data_schema=self._build_user_schema(self._library_user_id, user_options),
            errors=self._errors,
        )


class JellyfinOptionsFlowHandler(JellyfinFlowBase, config_entries.OptionsFlow):
    """Option flow for Jellyfin component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        super().__init__()
        self._errors: dict[str, str] = {}
        self._url = config_entry.data.get(CONF_URL)
        self._api_key = config_entry.data.get(CONF_API_KEY, "")
        self._verify_ssl = config_entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
        self._generate_upcoming = config_entry.data.get(CONF_GENERATE_UPCOMING, False)
        self._generate_yamc = config_entry.data.get(CONF_GENERATE_YAMC, False)
        self._library_user_id = config_entry.data.get(CONF_LIBRARY_USER_ID)

    async def async_step_init(self, user_input: dict[str, object] | None = None) -> ConfigFlowResult:
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input: dict[str, object] | None = None) -> ConfigFlowResult:
        self._errors = {}

        if user_input is not None:
            self._url = str(user_input[CONF_URL])
            self._api_key = user_input[CONF_API_KEY]
            self._verify_ssl = user_input[CONF_VERIFY_SSL]
            self._generate_upcoming = user_input[CONF_GENERATE_UPCOMING]
            self._generate_yamc = user_input[CONF_GENERATE_YAMC]
            needs_user = self._generate_upcoming or self._generate_yamc

            if needs_user:
                # Build with model_construct to defer validation until user is selected
                self._pending_entry_data = JellyfinEntryData.model_construct(
                    url=self._url,
                    api_key=self._api_key,
                    verify_ssl=self._verify_ssl,
                    generate_upcoming=self._generate_upcoming,
                    generate_yamc=self._generate_yamc,
                    library_user_id=self._library_user_id,
                )
                try:
                    self._client = await self.hass.async_add_executor_job(
                        self._authenticate_client,
                        self._url,
                        self._api_key,
                        self._verify_ssl,
                    )
                except (asyncio.TimeoutError, CannotConnect):
                    _LOGGER.error("cannot connect")
                    result = RESULT_CONN_ERROR
                    self._errors["base"] = result
                else:
                    return await self.async_step_select_user()
            else:
                self._library_user_id = None
                self._pending_entry_data = JellyfinEntryData(
                    url=self._url,
                    api_key=self._api_key,
                    verify_ssl=self._verify_ssl,
                    generate_upcoming=self._generate_upcoming,
                    generate_yamc=self._generate_yamc,
                    library_user_id=None,
                )
                return self._create_entry_from_pending(self._url)

        data_schema = {
            vol.Required(CONF_URL, default=self._url or ""): str,
            vol.Required(CONF_API_KEY, default=self._api_key): str,
            vol.Optional(CONF_VERIFY_SSL, default=self._verify_ssl): bool,
            vol.Optional(CONF_GENERATE_UPCOMING, default=self._generate_upcoming): bool,
            vol.Optional(CONF_GENERATE_YAMC, default=self._generate_yamc): bool,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )

    async def async_step_select_user(self, user_input: dict[str, object] | None = None) -> ConfigFlowResult:
        self._errors = {}

        if user_input is not None:
            raw_library_user_id = user_input.get(CONF_LIBRARY_USER_ID)
            if not raw_library_user_id:
                self._errors["base"] = ERROR_USER_REQUIRED
            elif self._pending_entry_data is None:
                raise ValueError("No pending entry data")
            else:
                library_user_id = str(raw_library_user_id)
                # Rebuild with user and validate
                self._pending_entry_data = JellyfinEntryData(
                    url=self._pending_entry_data.url,
                    api_key=self._pending_entry_data.api_key,
                    verify_ssl=self._pending_entry_data.verify_ssl,
                    generate_upcoming=self._pending_entry_data.generate_upcoming,
                    generate_yamc=self._pending_entry_data.generate_yamc,
                    library_user_id=library_user_id,
                )
                self._library_user_id = library_user_id
                return self._create_entry_from_pending(self._url)

        try:
            user_options = await self._async_get_user_options()
        except UserSelectionError:
            self._errors["base"] = ERROR_USER_FETCH
            user_options = []

        if not user_options:
            return self.async_show_form(
                step_id="select_user",
                data_schema=vol.Schema({}),
                errors=self._errors,
            )

        return self.async_show_form(
            step_id="select_user",
            data_schema=self._build_user_schema(self._library_user_id, user_options),
            errors=self._errors,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we can not connect."""
