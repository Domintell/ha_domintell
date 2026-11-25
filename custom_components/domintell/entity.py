"""Base entity for the Domintell integration."""

from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.entity import Entity

from .domintell_api.controllers.events import EventType


class DomintellEntity(Entity):
    """Common part of all Domintell entities: availability from the gateway connection.

    The child class must set `self._api` (the DomintellGateway) in its `__init__`
    and call `await super().async_added_to_hass()` in its `async_added_to_hass`.
    """

    @property
    def available(self) -> bool:
        """Return True if the connection with the gateway is open."""
        return self._api.is_connected

    async def async_added_to_hass(self) -> None:
        """Subscribe to the connection state of the gateway."""
        await super().async_added_to_hass()

        self.async_on_remove(
            self._api.events.subscribe(
                self._handle_connection_event,
                (EventType.CONNECTED, EventType.DISCONNECTED, EventType.RECONNECTED),
            )
        )

    @callback
    def _handle_connection_event(self, event_type: EventType, data=None) -> None:
        """Update the entity state when the connection state changes."""
        # pylint: disable=unused-argument

        self.async_write_ha_state()
