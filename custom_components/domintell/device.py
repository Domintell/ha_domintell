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
    ATTR_DEFAULT_NAME,
    ATTR_SUGGESTED_AREA,
)
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .domintell_api.controllers.events import EventType
from .domintell_api import DomintellGateway
from .domintell_api.gateway import gen_module_info
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
            # Look for the parent bridge in the registry
            if hasattr(dev_reg, "async_get_device_by_identifier"):
                parent_device = dev_reg.async_get_device_by_identifier(
                    identifier=(DOMAIN, bridge_id), config_entry_id=entry.entry_id
                )

                if parent_device:
                    params["via_device_id"] = parent_device.id

            else:
                # Support for older versions of HA (< 2026.8.0)
                params["via_device"] = (DOMAIN, bridge_id)

        return dev_reg.async_get_or_create(config_entry_id=entry.entry_id, **params)

    @callback
    def remove_device(device_id: str) -> None:
        """Remove device from registry."""

        if device := (
            dev_reg.async_get_device_by_identifier(
                identifier=(DOMAIN, device_id), config_entry_id=entry.entry_id
            )
            if hasattr(dev_reg, "async_get_device_by_identifier")
            else dev_reg.async_get_device(identifiers={(DOMAIN, device_id)})
        ):
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
    for device in dev_controller:
        add_device(device)

    # Remove what was deleted from the installation while Home Assistant was stopped
    async_remove_stale_entries(bridge)

    # add listener for updates on Domintell controllers
    entry.async_on_unload(dev_controller.subscribe(handle_device_event))


@callback
def async_remove_stale_entries(bridge: DomintellBridge) -> None:
    """Remove devices and entities that are no longer in the APPINFO.

    Must only be called once the APPINFO has been received (gateway.initialize()
    raises an error otherwise), so that the modules list is complete.
    """
    entry = bridge.config_entry
    hass = bridge.hass
    api: DomintellGateway = bridge.api

    if len(api.modules) == 0:
        # Incomplete data: never remove anything
        return

    # Only identifiers built by this integration are checked, others are never removed
    prefix = f"{entry.unique_id}_"

    # Devices to keep: the bridge and every module of the APPINFO
    known_devices = {f"{entry.unique_id}_{bridge.bridge_id}"}
    module_info = gen_module_info(entry.unique_id.upper())
    if module_info is not None:
        known_devices.add(f"{entry.unique_id}_{module_info['id']}")

    # Entities to keep: those whose IO is still in the APPINFO, whatever the module
    # they are attached to (unique_id is "<entry>_<module>_<io_id>[_<key>]")
    known_ios = set()
    for module in api.modules:
        known_devices.add(f"{entry.unique_id}_{module.id}")
        for io in module.values():
            known_ios.add(io.id)

    ent_reg = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        unique_id = entity.unique_id
        if not unique_id.startswith(prefix):
            continue
        parts = unique_id.split("_")
        if len(parts) >= 3 and parts[2] in known_ios:
            continue
        ent_reg.async_remove(entity.entity_id)

    dev_reg = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        device_ids = [
            device_id for domain, device_id in device.identifiers if domain == DOMAIN
        ]
        if not any(device_id.startswith(prefix) for device_id in device_ids):
            continue
        if any(device_id in known_devices for device_id in device_ids):
            continue
        # The gateway (DGQG0x / DNET0x) is never removed: a DNET can be missing
        # from the APPINFO, it is then created from the config entry data
        if (device.name or "").split("-")[0] in BRIDGES_LIST:
            continue
        # note: removal of the underlying entities is handled by core
        dev_reg.async_remove_device(device.id)
