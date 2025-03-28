"""Support for the Domintell system."""

import logging

_LOGGER = logging.getLogger(__name__)


from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.config_entries import ConfigEntry

from .bridge import DomintellBridge
from .const import DOMAIN
from .domintell_api.gateway import gen_module_info


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a config entry."""

    # Setup the bridge instance
    bridge = DomintellBridge(hass, config_entry)

    # Generate bridge informations
    module_serial_number_text = config_entry.unique_id.upper()
    module_info = gen_module_info(module_serial_number_text)

    # Add bridge to device registry
    if module_info is not None:
        bridge.bridge_id = module_info["serial_number"]
        device_id = f"{config_entry.unique_id}_{module_info["id"]}"
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, device_id)},
            serial_number=f"{module_info["module_number"]} ({module_info["serial_number"]})",
            name=module_info["name"],
            model=module_info["model"],
            sw_version=module_info["software_version"],
            manufacturer=module_info["manufacturer"],
        )

    config_entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, bridge.shutdown)
    )

    # Initialize bridge
    if not await bridge.async_initialize_bridge():
        return False

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_success = await hass.data[DOMAIN][config_entry.entry_id].async_reset()
    if len(hass.data[DOMAIN]) == 0:
        hass.data.pop(DOMAIN)
        # hass.services.async_remove(DOMAIN)
    return unload_success


# async def async_remove_entry(hass, config_entry) -> None:
#     """Handle removal of an entry."""
#     # If a component needs to clean up code when an entry is removed, it can define a removal method


# async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
#     """Migrate old entry."""
#     # If the config entry version is changed, async_migrate_entry must be implemented to support the migration of old entries.
#     # This is documented in detail in the config flow documentation
