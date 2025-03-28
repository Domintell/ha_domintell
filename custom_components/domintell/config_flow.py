"""Config flow to configure Domintell."""

from __future__ import annotations
import voluptuous as vol
import re
from typing import Any
from collections.abc import Mapping
import logging

_LOGGER = logging.getLogger(__name__)

from homeassistant.components import onboarding, zeroconf
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
)


from .const import (
    CONF_IGNORE_AVAILABILITY,
    DOMAIN,
    BRIDGES_LIST,
    DEFAULT_BRIDGE,
    CONF_MODULE_TYPE,
    CONF_MODULE_SN,
)
from .domintell_api import (
    DomintellGateway,
    MaxConnectedClient,
    InvalidCredentials,
    UserDatabaseEmpty,
    InvalidAppinfo,
)


def default_schema(user_input):
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=user_input.get(CONF_HOST)): str,
            vol.Optional(CONF_USERNAME, default=""): str,
            vol.Optional(CONF_PASSWORD, default=""): str,
        }
    )


def usr_pass_schema(user_input):
    # pylint: disable=unused-argument
    return vol.Schema(
        {
            vol.Optional(CONF_USERNAME, default=""): str,
            vol.Optional(CONF_PASSWORD, default=""): str,
        }
    )


def select_module_schema(user_input):
    # pylint: disable=unused-argument
    return vol.Schema(
        {
            vol.Required(CONF_MODULE_TYPE, default=DEFAULT_BRIDGE): vol.In(
                BRIDGES_LIST
            ),
            vol.Required(CONF_MODULE_SN, default=1): vol.All(
                vol.Coerce(int), vol.Range(min=0)
            ),
        }
    )


class DomintellConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Domintell config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the Domintell flow."""
        pass

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            device_unique_id = None
            host = user_input[CONF_HOST].rstrip(".")
            username = user_input[CONF_USERNAME] or ""
            password = user_input[CONF_PASSWORD] or ""

            try:
                device_info = await self._async_try_connect(host, username, password)
                device_unique_id = device_info["serial_number_text"].lower()
                self.name = device_unique_id.upper()
            except InvalidAppinfo as ex:
                # Case where the bridge does not appear in the list of modules
                pattern = r"^(dgqg|dnet)\d{2}-\d+\.local$"
                if re.match(pattern, host) is not None:
                    device_unique_id = host.replace(".local", "")
                else:
                    return await self.async_step_select_module(user_input)
            except InvalidCredentials as ex:
                errors["base"] = "invalid_credentials"
            except Exception as ex:
                _LOGGER.error(ex)
                raise AbortFlow(str(ex)) from ex

            if errors == {}:
                await self.async_set_unique_id(
                    device_unique_id, raise_on_progress=False
                )
                self._abort_if_unique_id_configured(updates=user_input)

                return self.async_create_entry(
                    title=f"Domintell {self.name}",
                    data=user_input,
                )

        user_input = user_input or {}

        return self.async_show_form(
            step_id="user",
            data_schema=default_schema(user_input),
            errors=errors,
        )

    async def async_step_select_module(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Module type and serial configuration."""
        errors = {}

        if user_input and (CONF_MODULE_TYPE in user_input):
            device_unique_id = (
                f"{user_input[CONF_MODULE_TYPE].lower()}-{user_input[CONF_MODULE_SN]}"
            )

            await self.async_set_unique_id(device_unique_id, raise_on_progress=False)
            self._abort_if_unique_id_configured(updates=user_input)

            return self.async_create_entry(
                title=f"Domintell {self.name}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="select_module",
            data_schema=select_module_schema(user_input),
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        errors = {}
        # _LOGGER.warning(f"---->discovery_info : {discovery_info}")

        # Check if the service type matches
        if discovery_info.type != "_domintellmodule._tcp.local.":
            return self.async_abort(reason="not_domintell_module")

        # Ignore if host is IPv6
        if discovery_info.ip_address.version == 6:
            return self.async_abort(reason="invalid_host")

        # Check that it is a Domintell master or dnet02
        if not (
            discovery_info.name.startswith("dgqg")
            or discovery_info.name.startswith("dnet")
        ):
            return self.async_abort(reason="not_domintell_bridge")

        self.ip = discovery_info.addresses[0]  # ip address V4
        self.host = discovery_info.hostname.rstrip(".")  # 'dgqg04-462.local'
        name = discovery_info.name  # 'dgqg04-462._domintellmodule._tcp.local.'

        index_premier_point = name.find(".")
        device_unique_id = name[:index_premier_point]  # ie: "dgqg02-253"
        self.name = device_unique_id.upper()

        # The installation can be equipped with a Master and a DNETx
        # In this case we must reject the master in the discoveries
        if discovery_info.name.startswith("dgqg"):
            # Connection attempt, if the master module is linked to a DNET,
            # it will explicitly refuse the connection
            try:
                await self._async_test_connection(self.ip)
            except ConnectionRefusedError as ex:
                return self.async_abort(reason="not_domintell_bridge")
            except Exception as ex:
                pass

        # Assign a unique ID to the flow and abort the flow
        # if another flow with the same unique ID is in progress
        await self.async_set_unique_id(device_unique_id)

        # Abort the flow if a config entry with the same unique ID exists
        self._abort_if_unique_id_configured(
            updates={CONF_HOST: discovery_info.host}, reload_on_update=True
        )

        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        errors = {}

        if user_input is not None or not onboarding.async_is_onboarded(self.hass):
            username = user_input[CONF_USERNAME] or ""
            password = user_input[CONF_PASSWORD] or ""

            try:
                await self._async_try_connect(self.ip, username, password)
            except InvalidAppinfo as ex:
                # ignore this type of error
                pass
            except InvalidCredentials as ex:
                errors["base"] = "invalid_credentials"
            except Exception as ex:
                _LOGGER.error(ex)
                raise AbortFlow(str(ex)) from ex

            if errors == {}:
                return self.async_create_entry(
                    title=f"Domintell {self.name}",
                    data={
                        CONF_HOST: self.host,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                    },
                )

        self._set_confirm_only()
        self.context["title_placeholders"] = {"name": self.name}

        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={
                "serial": self.name,
                CONF_HOST: self.ip,
            },
            data_schema=usr_pass_schema(user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        reauth_entry = self._get_reauth_entry()
        errors = {}

        if user_input is not None:
            host = reauth_entry.data[CONF_HOST]
            username = user_input[CONF_USERNAME] or ""
            password = user_input[CONF_PASSWORD] or ""

            try:
                await self._async_try_connect(host, username, password)
            except InvalidCredentials as ex:
                errors["base"] = "invalid_credentials"
            except Exception as ex:
                _LOGGER.error(ex)
                raise AbortFlow(str(ex)) from ex

            if errors == {}:
                return self.async_update_reload_and_abort(
                    reauth_entry, data_updates=user_input
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=usr_pass_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any]
    ) -> ConfigFlowResult:
        """Perform reconfigure upon an user action."""
        reconfigure_entry = self._get_reconfigure_entry()
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            username = user_input[CONF_USERNAME] or ""
            password = user_input[CONF_PASSWORD] or ""

            try:
                device_info = await self._async_try_connect(host, username, password)
                device_unique_id = device_info["serial_number_text"].lower()
            except InvalidAppinfo as ex:
                # Case where the bridge does not appear in the list of modules
                pattern = r"^(dgqg|dnet)\d{2}-\d+\.local$"
                if re.match(pattern, host) is not None:
                    device_unique_id = host.replace(".local", "")
                else:
                    return await self.async_step_select_module(user_input)

            except InvalidCredentials as ex:
                errors["base"] = "invalid_credentials"
                raise AbortFlow("invalid_credentials") from ex
            except Exception as ex:
                _LOGGER.error(ex)
                raise AbortFlow(str(ex)) from ex

            if errors == {}:
                await self.async_set_unique_id(device_unique_id)
                self._abort_if_unique_id_mismatch(reason="wrong_device")

                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data_updates=user_input,
                )

        return self.async_show_form(
            step_id="reconfigure",
            description_placeholders={"serial": reconfigure_entry.unique_id.upper()},
            data_schema=default_schema(reconfigure_entry.data),
            errors=errors,
        )

    @staticmethod
    async def _async_test_connection(host: str):
        """Test the websocket connection.

        Make connection with device to test the connection
        """
        gateway = DomintellGateway(host)
        await gateway.test_connection()

    @staticmethod
    async def _async_try_connect(
        host: str, username: str | None = None, password: str | None = None
    ):
        """Try to connect.

        Make connection with device to test the connection and recover information
        """
        gateway = DomintellGateway(host, username, password)

        try:
            await gateway.initialize(exit_on_error=True)

            # Determine which module we are connected to
            my_gateway = gateway.get_module_gateway

            if my_gateway is not None:
                return {
                    "id": my_gateway.id,
                    "serial_number": my_gateway.serial_number,
                    "serial_number_text": my_gateway.serial_number_text,
                }
            else:
                # Case where no Master and no DNET found in the modules list
                # Try to recover information from discover command in LP (only from LP Version 43.7)
                server_info = gateway._client.server_info
                if server_info is not None:
                    return {
                        "id": server_info["id"],
                        "serial_number": server_info["serial_number"],
                        "serial_number_text": server_info["serial_number_text"],
                    }

                raise InvalidAppinfo("no_bridges")

        except (InvalidCredentials, UserDatabaseEmpty) as ex:
            raise InvalidCredentials("invalid_credentials") from ex
        except ConnectionRefusedError as ex:
            raise ConnectionRefusedError("connection_refused") from ex
        except MaxConnectedClient as ex:
            raise MaxConnectedClient("max_connection") from ex
        except TimeoutError as ex:
            raise TimeoutError("network_error") from ex
        except Exception as ex:
            raise type(ex)(str(ex)) from ex
        finally:
            await gateway.close()


class DomintellOptionsFlowHandler(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage Domintell options."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # create a list of Domintell device ID's that the user can select
        # to ignore availability status
        dev_reg = dr.async_get(self.hass)
        entries = dr.async_entries_for_config_entry(dev_reg, self.config_entry.entry_id)
        dev_ids = {
            identifier[1]: entry.name
            for entry in entries
            for identifier in entry.identifiers
            if identifier[0] == DOMAIN
        }
        # filter any non existing device id's from the list
        cur_ids = [
            item
            for item in self.config_entry.options.get(CONF_IGNORE_AVAILABILITY, [])
            if item in dev_ids
        ]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_IGNORE_AVAILABILITY,
                        default=cur_ids,
                    ): cv.multi_select(dev_ids),
                }
            ),
        )
