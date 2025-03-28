"""Diagnostics support for Domintell."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .bridge import DomintellBridge
from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    bridge: DomintellBridge = hass.data[DOMAIN][entry.entry_id]
    return await bridge.api.get_diagnostics()


# async def async_get_device_diagnostics(
#     hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
# ) -> dict[str, Any]:
#     """Return diagnostics for a device."""

#     bridge: DomintellBridge = hass.data[DOMAIN][entry.entry_id]
#     return await bridge.api.get_diagnostics()
