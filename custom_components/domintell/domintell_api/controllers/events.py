from collections import deque
from collections.abc import Callable
from enum import Enum
import copy
import asyncio
from asyncio.coroutines import iscoroutinefunction
from typing import TypedDict
import time
from uuid import uuid4

from ..const import IO_DEFAULT_TARGET_TYPES
from ..lightprotocol import LpStatus
from ..websocket import ConnectionState


class ResourceTypes(Enum):
    """
    Type of the supported resources.

    """

    GATEWAY = "gateway"
    MODULE = "module"
    SWITCH = "switch"
    MOMENTARY_SWITCH = "momentary_switch"
    LIGHT = "light"
    COVER = "cover"
    FAN = "fan"
    SENSOR = "sensor"
    SCENE = "scene"
    BUTTON = "button"
    TEMPERATURE = "temperature"
    ANALOG = "analog"
    ILLUMINANCE = "illuminance"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    CO2 = "carbon_dioxide"
    WIND = "wind"
    POWER_SUPPLY = "power_supply"
    ELECTRICITY = "electricity"
    MOTION = "motion"
    CONTACT = "contact"
    TAMPER = "tamper"
    VARIABLE = "variable"
    GROUP = "group"

    UNKNOWN = "unknown"


class EventType(Enum):
    """Enum with possible Events."""

    RESOURCE_ADDED = "add"
    RESOURCE_UPDATED = "update"
    RESOURCE_DELETED = "delete"

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTED = "reconnected"


class DomintellEvent(TypedDict):
    """Domintell Event message as emitted."""

    id: str
    creationtime: str
    type: str
    data: list[dict]


EventCallBackType = Callable[[EventType, dict | None], None]
EventSubscriptionType = tuple[
    EventCallBackType,
    "tuple[EventType] | None",
    "tuple[ResourceTypes] | None",
]


class EventsController:
    """Controller holding and managing Domintell events."""

    def __init__(self, gateway) -> None:
        """Initialize instance."""
        self._gateway = gateway
        self._logger = gateway._logger
        self._subscribers: list[EventSubscriptionType] = []
        self._status = ConnectionState.DISCONNECTED
        self._bg_tasks: list[asyncio.Task] = []
        self._event_queue = asyncio.Queue()
        self._event_history = deque(maxlen=25)

    @property
    def connected(self) -> bool:
        """Return bool if we're connected."""
        return self._status in (ConnectionState.LOGGED, ConnectionState.RELOGGED)

    @property
    def status(self) -> bool:
        """Return connection status."""
        return self._status

    @property
    def last_events(self) -> list[dict]:
        """Return a list with the previous X messages."""
        return self._event_history

    def initialize(self) -> None:
        """Initialize events."""
        self._gateway._client.on_connection_state_change(self.__connection_state_change)
        self._gateway._client.on_status(self.__status_handler)
        assert len(self._bg_tasks) == 0
        # self._bg_tasks.append(asyncio.create_task(self.__event_reader()))
        self._bg_tasks.append(asyncio.create_task(self.__event_processor()))

    async def stop(self) -> None:
        """Stop listening for events."""
        for task in self._bg_tasks:
            task.cancel()
        self._bg_tasks = []

    def subscribe(
        self,
        callback: EventCallBackType,
        event_filter: EventType | tuple[EventType] | None = None,
        resource_filter: ResourceTypes | tuple[ResourceTypes] | None = None,
    ) -> Callable:
        """
        Subscribe to events emitted by the Domintell bridge for resources.

        Parameters:
            - `callback` - callback function to call when an event emits.
            - `event_filter` - Provide an EventType as filter (Optional).
            - `resource_filter` - Provide a ResourceType as filter (Optional).

        Returns:
            function to unsubscribe.
        """
        if not isinstance(event_filter, None | tuple):
            event_filter = (event_filter,)
        if not isinstance(resource_filter, None | tuple):
            resource_filter = (resource_filter,)
        subscription = (callback, event_filter, resource_filter)

        def unsubscribe():
            self._subscribers.remove(subscription)

        self._subscribers.append(subscription)
        return unsubscribe

    def emit(self, event_type: EventType, data: dict | None = None) -> None:
        """Emit event to all listeners."""
        for callback, event_filter, resource_filter in self._subscribers:
            if event_filter is not None and event_type not in event_filter:
                continue
            if (
                data is not None
                and resource_filter is not None
                and ResourceTypes(data.get("type")) not in resource_filter
            ):
                continue
            if iscoroutinefunction(callback):
                asyncio.create_task(callback(event_type, data))
            else:
                callback(event_type, data)

    def __connection_state_change(self, state: ConnectionState) -> None:
        self._logger.info(f"Connection state as changed to: {state}")

        self._status = state

        if state == ConnectionState.LOGGED:
            type_of_event = EventType.CONNECTED
        elif state == ConnectionState.DISCONNECTED:
            type_of_event = EventType.DISCONNECTED
        elif state == ConnectionState.RELOGGED:
            type_of_event = EventType.RECONNECTED
        else:
            # Do nothing
            return

        websocket_event = {
            "id": uuid4(),
            "creationtime": time.time(),
            "type": type_of_event,
            "data": [],
        }
        event: DomintellEvent = DomintellEvent(websocket_event)
        self._event_queue.put_nowait(event)
        self._event_history.append(event)

    def __status_handler(self, status_list: list[LpStatus]) -> None:

        for status in status_list:
            data: list = []
            muliple_sub_status = []
            # print(f"\nNew status (raw message): '{status.message}'")
            # print(status)

            # Split data in atomic event
            if (
                status.io_type not in [8, 12, 16, 17, 24, 25, 29, 41, 46, 51, 60]
                and len(status.data) > 1
            ):
                # Case of module_type PRL number of io is configurable
                module_of_io = self._gateway.modules.get_module(status.serial_number)

                if module_of_io is None:
                    # This IO is not part of any module
                    continue

                nbr_of_bool_io = len(module_of_io.get_ios_by_type(status.io_type))

                for index, element in enumerate(status.data):
                    if (nbr_of_bool_io is not None) and ((index + 1) > nbr_of_bool_io):
                        break
                    try:
                        sub_status = copy.deepcopy(status)
                        parts = status._id.rsplit("-", 1)
                        sub_status._io_offset += index
                        sub_status._id = parts[0] + "-" + str(sub_status._io_offset)
                        sub_status._data = [element]
                        sub_status._raw_data = str(element)

                        muliple_sub_status.append(sub_status)
                    except Exception as ex:
                        print(
                            f"Error split {status.module_type} status into sub-status for data[{index}]: {ex}"
                        )
                        continue
            else:
                muliple_sub_status.append(status)

            # Here we have a list of unitary status
            for item in muliple_sub_status:
                status_dic = item.get_dict

                # Determine target type
                target_type = IO_DEFAULT_TARGET_TYPES.get(
                    status_dic["io_type"], "unknown"
                )

                status_dic["type"] = ResourceTypes(target_type)
                data.append(status_dic)

            dom_event = {
                "id": status.id,
                "creationtime": time.time(),
                "type": EventType.RESOURCE_UPDATED,
                "data": data,
            }

            event: DomintellEvent = DomintellEvent(dom_event)
            self._event_queue.put_nowait(event)
            self._event_history.append(event)

    async def __event_processor(self) -> None:
        """Process incoming Domintell events on the Queue and distribute those."""
        while True:
            event: DomintellEvent = await self._event_queue.get()

            if len(event["data"]) == 0:
                self.emit(EventType(event["type"]))
            else:
                for item in event["data"]:
                    self.emit(EventType(event["type"]), item)
