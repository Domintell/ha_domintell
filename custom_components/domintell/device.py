"""Handles Domintell resource of type `device` mapping to Home Assistant device."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import (
    ATTR_IDENTIFIERS,
    ATTR_SERIAL_NUMBER,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_MODEL_ID,
    ATTR_NAME,
    ATTR_SW_VERSION,
    ATTR_HW_VERSION,
    ATTR_CONNECTIONS,
    ATTR_VIA_DEVICE,
    ATTR_DEFAULT_NAME,
    ATTR_SUGGESTED_AREA,
)
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr

from .domintell_api.controllers.events import EventType
from .domintell_api import DomintellGateway
from .const import DOMAIN, BRIDGES_LIST

if TYPE_CHECKING:
    from .bridge import DomintellBridge


async def async_setup_devices(bridge: DomintellBridge):
    """Manage setup of devices from Domintell devices."""
    entry = bridge.config_entry
    hass = bridge.hass
    api: DomintellGateway = bridge.api
    dev_reg = dr.async_get(hass)
    dev_controller = api.modules

    @callback
    def add_device(resource) -> dr.DeviceEntry:
        """Register a Domintell device in device registry."""
        # Register a Domintell device resource as device in HA device registry.
        bridge_id = f"{entry.unique_id}_{bridge.bridge_id}"  # ie: "dgqg04-253_520000FD"
        device_id = f"{entry.unique_id}_{resource.id}"  # ie: "dgqg04-253_0A0012BF"

        params = {
            ATTR_IDENTIFIERS: {(DOMAIN, device_id)},  # ie "dgqg04-253_0600052F"
            ATTR_SERIAL_NUMBER: f"{resource.module_number} ({resource.serial_number})",
            ATTR_SW_VERSION: resource.software_version,
            # ATTR_HW_VERSION: # TODO Not available at the moment
            ATTR_NAME: resource.name,  # ie "DBIR01-1327" or "DDBIR01-1327-VIRTUAL"
            ATTR_MODEL: resource.model,  # ie "DBIR01" or "DBIR01-VIRTUAL"
            # ATTR_MODEL_ID: resource.model,  # TODO (appears in parentheses)
            ATTR_MANUFACTURER: resource.manufacturer,  # "Domintell"
        }

        # Add via_device if necessary
        if device_id != bridge_id:
            params[ATTR_VIA_DEVICE] = (DOMAIN, bridge_id)

        return dev_reg.async_get_or_create(config_entry_id=entry.entry_id, **params)

    @callback
    def remove_device(device_id: str) -> None:
        """Remove device from registry."""

        if device := dev_reg.async_get_device(identifiers={(DOMAIN, device_id)}):
            # note: removal of any underlying entities is handled by core
            dev_reg.async_remove_device(device.id)

    @callback
    def handle_device_event(evt_type: EventType, resource) -> None:
        """Handle event from Domintell controller."""
        if evt_type == EventType.RESOURCE_DELETED:
            device_id = f"{entry.unique_id}_{resource.id}"
            remove_device(device_id)
        else:
            # updates to existing device will also be handled by this call
            add_device(resource)

    # Create/update all current devices found in controllers
    known_devices = [add_device(device) for device in dev_controller]

    # Check for nodes that no longer exist and remove them
    for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        if device not in known_devices:
            # Workaround for case the bridge is not in the list of discovered devices
            if device.name.split("-")[0] not in BRIDGES_LIST:
                dev_reg.async_remove_device(device.id)

    # add listener for updates on Domintell controllers
    entry.async_on_unload(dev_controller.subscribe(handle_device_event))
