"""Code to handle a Domintell bridge."""

from __future__ import annotations

import asyncio
import logging


from homeassistant.core import callback, Event
from homeassistant import core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
)

from .const import DOMAIN, PLATFORMS
from .device import async_setup_devices
from .dom_event import async_setup_domintell_events
from .domintell_api import DomintellGateway, InvalidCredentials, UserDatabaseEmpty


class DomintellBridge:
    """Manages a single domintell bridge."""

    def __init__(self, hass: core.HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the system."""
        self.config_entry = config_entry
        self.hass = hass
        self.authorized = False
        # Jobs to be executed when API is reset.
        self.reset_jobs: list[core.CALLBACK_TYPE] = []
        self.logger = logging.getLogger(__name__)
        # Store actual api connection to bridge as api
        username: str = self.config_entry.data[CONF_USERNAME]
        password: str = self.config_entry.data[CONF_PASSWORD]
        self.api = DomintellGateway(self.host, username, password)
        self._bridge_id = ""
        # Store (this) bridge object in hass data
        hass.data.setdefault(DOMAIN, {})[self.config_entry.entry_id] = self

    @property
    def bridge_id(self) -> str | None:
        """Return the ID of the bridge we're currently connected to."""
        if self.api.gateway_id is not None:
            return self.api.gateway_id
        else:
            return self._bridge_id

    @bridge_id.setter
    def bridge_id(self, id: str) -> None:
        self._bridge_id = id

    @property
    def host(self) -> str:
        """Return the host of this bridge."""
        return self.config_entry.data[CONF_HOST]

    async def async_initialize_bridge(self) -> bool:
        """Initialize Connection with the Domintell API."""
        setup_ok = False
        try:
            async with asyncio.timeout(10):
                await self.api.initialize()
            setup_ok = True
        except (InvalidCredentials, UserDatabaseEmpty) as ex:
            # Username and password can become invalid if configuration in module is reset or user removed.
            raise ConfigEntryAuthFailed(
                "Invalid credentials for Domintell bridge"
            ) from ex
        except (asyncio.TimeoutError, TimeoutError) as ex:
            raise ConfigEntryNotReady(
                f"Timed out while connecting to Domintell bridge at {self.host}"
            ) from ex
        except Exception as ex:
            raise ConfigEntryNotReady(ex) from ex
        finally:
            if not setup_ok:
                await self.api.close()

        await async_setup_devices(self)
        await async_setup_domintell_events(self)
        await self.hass.config_entries.async_forward_entry_setups(
            self.config_entry, PLATFORMS
        )

        # Add listener for config entry updates.
        self.reset_jobs.append(self.config_entry.add_update_listener(_update_listener))
        self.authorized = True
        return True

    @callback
    async def shutdown(self, event: Event) -> None:
        """Wrap the call to api.close.

        Used as an argument to EventBus.async_listen_once.
        """
        # pylint: disable=unused-argument

        await self.api.close()

    async def async_reset(self) -> bool:
        """Reset this bridge to default state.

        Will cancel any scheduled setup retry and will unload
        the config entry.
        """

        if self.api is None:
            return True

        await self.api.close()

        while self.reset_jobs:
            self.reset_jobs.pop()()

        # Unload platforms
        unload_success = await self.hass.config_entries.async_unload_platforms(
            self.config_entry, PLATFORMS
        )

        if unload_success:
            self.hass.data[DOMAIN].pop(self.config_entry.entry_id)

        return unload_success


async def _update_listener(hass: core.HomeAssistant, entry: ConfigEntry) -> None:
    """Handle ConfigEntry options update."""
    await hass.config_entries.async_reload(entry.entry_id)


# def create_config_flow(hass: core.HomeAssistant, host: str) -> None:
#     """Start a config flow."""
#     hass.async_create_task(
#         hass.config_entries.flow.async_init(
#             DOMAIN,
#             context={"source": SOURCE_IMPORT},
#             data={"host": host},
#         )
#     )
