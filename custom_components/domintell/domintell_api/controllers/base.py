import asyncio
from asyncio.coroutines import iscoroutinefunction
from collections.abc import Callable
from .events import EventCallBackType, EventType, ResourceTypes


EventSubscriptionType = tuple[
    EventCallBackType,
    "tuple[EventType] | None",
]

ID_FILTER_ALL = "*"


class BaseController:
    item_type: ResourceTypes | None = None

    def __init__(self, gateway) -> None:
        self._items: dict = {}
        self._subscribers: dict[str, EventSubscriptionType] = {ID_FILTER_ALL: []}
        self._gateway = gateway
        self._logger = self._gateway._logger
        self._initialized = False

    @property
    def items(self) -> list:
        return self.values()

    def get_io(self, id: str):
        """Get IO by id."""
        return self._items.get(id, None)

    def add_item(self, id: str, value):
        self._items[id] = value

    def remove_item(self, id: str):
        self._items.pop(id, None)

    def values(self) -> list:
        return list(self._items.values())

    def keys(self) -> list:
        return list(self._items.keys())

    def __getitem__(self, id: str):
        return self._items[id]

    def __iter__(self):
        return iter(self._items.values())

    def __len__(self):
        return len(self.values())

    def subscribe(
        self,
        callback: EventCallBackType,
        id_filter: str | tuple[str] | None = None,
        event_filter: EventType | tuple[EventType] | None = None,
    ) -> Callable:
        """
        Subscribe to status changes for this resource type.

        Parameters:
            - `callback` - callback function to call when an event emits.
            - `id_filter` - Optionally provide resource ID(s) to filter events for.
            - `event_filter` - Optionally provide EventType(s) as filter.

        Returns:
            function to unsubscribe.
        """
        if not isinstance(event_filter, None | list | tuple):
            event_filter = (event_filter,)

        if id_filter is None:
            id_filter = (ID_FILTER_ALL,)
        elif not isinstance(id_filter, list | tuple):
            id_filter = (id_filter,)

        subscription = (callback, event_filter)

        for id_key in id_filter:
            if id_key not in self._subscribers:
                self._subscribers[id_key] = []
            self._subscribers[id_key].append(subscription)

        # unsubscribe logic
        def unsubscribe():
            for id_key in id_filter:
                if id_key not in self._subscribers:
                    continue
                self._subscribers[id_key].remove(subscription)

        return unsubscribe

    async def initialize(self) -> None:
        """Initialize controller."""

        for module in self._gateway.modules.values():
            for io in module.values():
                if io.target_type == self.item_type.value:
                    await self._handle_event(
                        EventType.RESOURCE_ADDED, {"id": io.id, "instance": io}
                    )

        # subscribe to item updates
        self._gateway.events.subscribe(
            self._handle_event, resource_filter=self.item_type
        )

        self._initialized = True

    async def update(self, ios_removed, ios_added):
        """Update controller IO."""

        for io in ios_removed:
            if io["target_type"] == self.item_type.value:
                await self._handle_event(EventType.RESOURCE_DELETED, {"id": io["id"]})

        for io in ios_added:
            if io["target_type"] == self.item_type.value:
                instance = self._gateway.modules.get_io(io["id"])
                if instance is not None:
                    await self._handle_event(
                        EventType.RESOURCE_ADDED, {"id": io["id"], "instance": instance}
                    )

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""

        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_ADDED:
            # new item added
            item_instance = event_data["instance"]
            self.add_item(item_id, item_instance)
            current_item = self._items[item_id]
        elif event_type == EventType.RESOURCE_DELETED:
            # Existing item deleted
            current_item = self._items.pop(item_id, None)
        elif event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            current_item = self._items.get(item_id)
            if current_item is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    "Controller received update for unknown io %s", item_id
                )
                return
        else:
            pass

        if current_item is not None:
            subscribers = (
                self._subscribers.get(item_id, []) + self._subscribers[ID_FILTER_ALL]
            )

            for callback, event_filter in subscribers:
                if event_filter is not None and event_type not in event_filter:
                    continue
                # Dispatch the full resource object to the callback
                if iscoroutinefunction(callback):
                    asyncio.create_task(callback(event_type, current_item))
                else:
                    callback(event_type, current_item)
