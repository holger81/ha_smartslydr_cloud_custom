"""Adds config flow for SmartSlydr."""
from __future__ import annotations
from collections import OrderedDict
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.core import callback

from .api import (
    LycheeThingsApiClient,
    LycheeThingsApiClientAuthenticationError,
    LycheeThingsApiClientCommunicationError,
    LycheeThingsApiClientError,
)
from .const import DOMAIN, LOGGER

class SmartSlydrBaseFlowHandler(config_entries.ConfigFlow):  # noqa: D101
    async def _test_credentials(self, username: str, password: str) -> bool:
        """Validate credentials. Returns True if valid, False otherwise."""
        client = LycheeThingsApiClient(
            username,
            password,
            async_create_clientsession(self.hass),
        )

        if not await client.getSecurityTokens():
            return False
        return True

    # Options Flow
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Set Options flow for SmartSlydr Cloud Custom."""
        return SmartSlydrOptionsFlowHandler(config_entry)

class SmartSlydrFlowHandler(SmartSlydrBaseFlowHandler, domain=DOMAIN):
    """Config flow for SmartSlydr Cloud Custom."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                if not await self._test_credentials(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                ):
                    _errors["base"] = "auth"
                else:
                    return self.async_create_entry(
                        title=user_input[CONF_USERNAME],
                        data=user_input,
                    )
            except LycheeThingsApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except LycheeThingsApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except LycheeThingsApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        ),
                    ),
                }
            ),
            errors=_errors,
            description_placeholders={
                "url": "https://github.com/holger81/ha_smartslydr_cloud_custom",
            },
        )


class SmartSlydrOptionsFlowHandler(
    SmartSlydrBaseFlowHandler, config_entries.OptionsFlow
):
    """SmartSlydr Cloud Custom Option Flow Handler Class."""

    def __init__(self, config_entry):
        """Initialize SmartSlydr options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)
        self._errors = {}
        self._data = {}

    async def async_step_init(self):
        """Option flow for SmartSlydr Cloud Custom initialized by user."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Option flow for SmartSlydr Cloud Custom handler for user actions."""
        if user_input is not None:
            self._data = user_input
            return await self._update_options()

        data_schema = OrderedDict()
        data_schema[
            vol.Required("username", default=self.config_entry.data.get(CONF_USERNAME))
        ] = str
        data_schema[vol.Required("password", default="")] = str

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )

    async def _update_options(self):
        """Update config entry options."""
        try:
            valid = await self._test_credentials(
                self._data[CONF_USERNAME],
                self._data[CONF_PASSWORD],
            )
            if valid:
                return self.async_create_entry(
                    title=self.config_entry.data.get(CONF_USERNAME), data=self._data
                )
            self._errors["base"] = "invalid_credentials"
        except LycheeThingsApiClientAuthenticationError as exception:
            LOGGER.warning(exception)
            self._errors["base"] = "invalid_credentials"
        except LycheeThingsApiClientCommunicationError as exception:
            LOGGER.error(exception)
            self._errors["base"] = "connection"
        except LycheeThingsApiClientError as exception:
            LOGGER.exception(exception)
            self._errors["base"] = "unknown"
        return await self.async_step_user()
