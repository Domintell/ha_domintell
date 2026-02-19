import asyncio
import time
from collections.abc import Callable
import logging
from typing import Any

from .const import get_module_type_num_by_model
from .websocket import DomintellClient
from .lightprotocol import LpAppInfo
from .controllers.events import EventCallBackType, EventType
from .controllers.modules import ModulesController
from .controllers.switches import SwitchesController, MomentarySwitchesController
from .controllers.lights import LightsController
from .controllers.covers import CoversController
from .controllers.fans import FansController
from .controllers.sensors import SensorsController
from .controllers.scenes import ScenesController
from .controllers.variables import VariablesController
from .controllers.groups import GroupsController
from .controllers.events import EventsController


_LOGGER = logging.getLogger(__name__)


def gen_module_info(serial_number_text):
    module_info = {}

    try:
        parts = serial_number_text.upper().split("-")  # "DGQG04-253"
        module_model = parts[0]  # ie:"DGQG04"
        module_type_num = get_module_type_num_by_model(module_model)  # "54"
        module_number = int(parts[1])  # ie: 253
        module_number_text = hex(module_number)[2:].upper().zfill(6)  # ie: "0000FD"
        module_serial_number = f"{module_type_num}{module_number_text}"  # "540000FD"

        module_info["id"] = module_serial_number
        module_info["serial_number"] = module_serial_number
        module_info["module_number"] = module_number
        module_info["model"] = module_model
        module_info["name"] = serial_number_text
        module_info["manufacturer"] = "Domintell"
        module_info["software_version"] = None
    except Exception as ex:
        _LOGGER.warning(f"ERROR gen_module_info : {ex}")
        return None
    else:
        return module_info


def get_changed_dictionaries(old_list, new_list):

    def indexer_list(liste):
        return {element["id"]: element for element in liste if element is not None}

    old_list_indexee: dict = indexer_list(old_list)
    new_list_indexee: dict = indexer_list(new_list)

    added_elements = []
    removed_elements = []

    for id, element1 in old_list_indexee.items():
        if id in new_list_indexee:
            element2 = new_list_indexee[id]
            for field in element1:
                if field != "id":
                    if field == "extra_info":
                        if element1.get(field) != element2.get(field):
                            if not (
                                len(element1.get(field, []))
                                == len(element2.get(field, []))
                                and all(
                                    x in element2.get(field, [])
                                    for x in element1.get(field, [])
                                )
                            ):
                                removed_elements.append(element1)
                                added_elements.append(element2)
                                break
                    elif element1.get(field) != element2.get(field):
                        removed_elements.append(element1)
                        added_elements.append(element2)
                        break
        else:
            # Deleted items
            removed_elements.append(element1)

    # Added items
    for id, element2 in new_list_indexee.items():
        if id not in old_list_indexee:
            added_elements.append(element2)

    return removed_elements, added_elements


class DomintellGateway:
    """Control Domintell installation with LightProtocol API."""

    def __init__(
        self, host, username: str | None = None, password: str | None = None
    ) -> None:
        self._logger = logging.getLogger(f"{__package__}[{host}]")
        self._host = host
        self._port: int = 17481
        self._client: DomintellClient = DomintellClient(
            self._host, self._port, username, password
        )
        self._app: LpAppInfo | None = None
        self._module_gateway: Any | None = None

        # Controllers
        self._modules = ModulesController(self)
        self._switches = SwitchesController(self)
        self._momentary_switches = MomentarySwitchesController(self)
        self._lights = LightsController(self)
        self._covers = CoversController(self)
        self._fans = FansController(self)
        self._sensors = SensorsController(self)
        self._scenes = ScenesController(self)
        self._variables = VariablesController(self)
        self._groups = GroupsController(self)
        self._events = EventsController(self)
        self._disconnect_timestamp = 0
        self._initialized = False

        # Set websocket client callback
        self._client.on_appinfo(self._appinfo_handler)

    @property
    def is_connected(self) -> bool:
        return self._client.is_connected

    @property
    def gateway_id(self) -> str | None:
        """Return the ID of the gateway we're currently connected to."""
        if self._module_gateway is not None:
            return self._module_gateway.id
        else:
            # Try to recover information from discover command in LP (only from LP Version 43.7)
            server_info = self._client.server_info
            if server_info is not None:
                return server_info["id"]

        return None

    @property
    def get_module_gateway(self):
        """Return the gateway module we're currently connected to."""
        return self._module_gateway

    @property
    def host(self) -> str:
        """Return the hostname of the gateway."""
        return self._host

    @property
    def modules(self) -> ModulesController:
        """Get the Modules Controller for managing all module resources."""
        return self._modules

    @property
    def switches(self) -> SwitchesController:
        """Get the Switches Controller for managing all switch resources."""
        return self._switches

    @property
    def momentary_switches(self) -> MomentarySwitchesController:
        """Get the Switches Controller for managing all momentary switch resources."""
        return self._momentary_switches

    @property
    def lights(self) -> LightsController:
        """Get the Lights Controller for managing all light resources."""
        return self._lights

    @property
    def covers(self) -> CoversController:
        """Get the Covers Controller for managing all cover resources."""
        return self._covers

    @property
    def fans(self) -> FansController:
        """Get the Fans Controller for managing all fan resources."""
        return self._fans

    @property
    def sensors(self) -> SensorsController:
        """Get the Sensors Controller for managing all sensor resources."""
        return self._sensors

    @property
    def scenes(self) -> ScenesController:
        """Get the Scenes Controller for managing all scene resources."""
        return self._scenes

    @property
    def variables(self) -> VariablesController:
        """Get the Variables Controller for managing all scene resources."""
        return self._variables

    @property
    def groups(self) -> GroupsController:
        """Get the Groups Controller for managing all scene resources."""
        return self._groups

    @property
    def events(self) -> EventsController:
        """Get the Events Controller for managing all event resources."""
        return self._events

    async def test_connection(self):
        await self._client.test_connection(self._host, self._port)

    async def initialize(self, exit_on_error: bool = False) -> None:
        """Initialize the connection to the gateway and fetch all data."""
        self._initialized = False

        # Start event listener
        self._events.initialize()

        # Subscribe to connection state event
        self._events.subscribe(
            self._handle_connect_event, (EventType.RECONNECTED, EventType.DISCONNECTED)
        )

        # Initialize the connection with the gateway
        await self._client.connect(exit_on_error)

        # Request APPINFO
        await self._client.request_appinfo()

        # Wait initialization from appinfo is finished
        start_time = time.time()
        while not self._initialized:
            await asyncio.sleep(0.1)
            if time.time() - start_time > 5:
                return

    async def close(self) -> None:
        """Close connection and cleanup."""

        await self._client.disconnect()
        await self.events.stop()

    async def _appinfo_handler(self, appinfo: str) -> None:
        """Initialize all controllers."""

        self._logger.debug(f"APPINFO received: {appinfo}")
        # First line gives information about the DAP/configuration file
        # ie: "(PROG M 42.3 00/00/00 00h00 Rev=2 CP=UTF8) => MyHome Name :"

        try:
            # The gateway is already configured
            if self._initialized:
                new_app = LpAppInfo(appinfo)

                io_removed, io_added = get_changed_dictionaries(
                    self._app.ios, new_app.ios
                )

                if len(io_removed) > 0 or len(io_added) > 0:
                    # Update each controllers
                    # Note: It is essential to perform the modules controller update before the others controllers
                    await self._modules.update(io_removed, io_added)
                    await self._switches.update(io_removed, io_added)
                    await self._momentary_switches.update(io_removed, io_added)
                    await self._lights.update(io_removed, io_added)
                    await self._covers.update(io_removed, io_added)
                    await self._fans.update(io_removed, io_added)
                    await self._sensors.update(io_removed, io_added)
                    await self._scenes.update(io_removed, io_added)
                    await self._variables.update(io_removed, io_added)
                    await self._groups.update(io_removed, io_added)

                    self._app = new_app

                # Request current status of all IO
                await self.fetch_full_state()

                return
            else:
                self._app = LpAppInfo(appinfo)
        except Exception as ex:
            self._logger.error(f"Error parsing appinfo : {ex}")
            return

        self._logger.debug(f"Installation name: {self._app.name}")
        self._logger.debug(f"Lightprotocol version: {self._app.lp_version}")
        # self._logger.debug(f"IOs: {self._app.ios}")

        # Validate version
        major_version = self._app.lp_version_major
        minor_version = self._app.lp_version_minor
        revision_version = self._app.lp_version_revision

        # TODO Validate that we are greater than or equal to v 43.0.0 for example

        # Initialize
        # Note: It is essential to perform the modules controller initialization before the others controllers
        await self._modules.initialize(self._app.ios)
        await self._switches.initialize()
        await self._momentary_switches.initialize()
        await self._lights.initialize()
        await self._covers.initialize()
        await self._fans.initialize()
        await self._sensors.initialize()
        await self._scenes.initialize()
        await self._variables.initialize()
        await self._groups.initialize()

        # Determine which module we are connected to
        self._module_gateway = self._get_module_gateway()

        self._initialized = True

        # Request current status of all IO
        await self.fetch_full_state()

    def _get_module_gateway(self):
        """Determine which module we are connected to"""

        # List of Master and DNET modules
        master_list = self.modules.get_modules_master()
        dnet_list = self.modules.get_modules_dnet()

        if len(dnet_list) > 0:
            my_dnet = min(dnet_list, key=lambda module: int(module.serial_number, 16))
        else:
            my_dnet = None

        if len(master_list) > 0:
            my_master = min(
                master_list, key=lambda module: int(module.serial_number, 16)
            )
        else:
            my_master = None

        module_gateway = my_dnet if my_dnet else (my_master if my_master else None)

        return module_gateway

    async def _handle_connect_event(
        self,
        event_type: EventType,
        item: Any = None,
    ) -> None:
        """Handle (disconnect) event from the websocket."""
        # pylint: disable=unused-argument

        self._logger.info(f"Connection state as changed to: {event_type}")

        if event_type == EventType.DISCONNECTED:
            # If we receive a disconnect event, we store the timestamp
            self._disconnect_timestamp = time.time()
            # TODO see to send an error event to HA
        elif event_type == EventType.RECONNECTED:
            # If the time between the disconnect and reconnect is more than 2 seconds,
            # We ask for the appinfo else we fetch the full state.
            if (time.time() - self._disconnect_timestamp) > 2:
                # Request APPINFO
                self._logger.info("Request APPINFO")
                await self._client.request_appinfo()
            else:
                # We fetch the full state.
                self._logger.info("Refetch all IO status")
                await self.fetch_full_state()
        else:
            pass

    async def fetch_full_state(self) -> None:
        """Fetch state on all controllers."""
        await self._client.request_all_status()

    def subscribe(
        self,
        callback: EventCallBackType,
    ) -> Callable:
        """
        Subscribe to status changes for all resources.

        Returns:
            function to unsubscribe.
        """
        unsubscribes = [
            self.modules.subscribe(callback),
            self.switches.subscribe(callback),
            self._momentary_switches.subscribe(callback),
            self.lights.subscribe(callback),
            self.covers.subscribe(callback),
            self._fans.subscribe(callback),
            self.sensors.subscribe(callback),
            self.scenes.subscribe(callback),
            self.variables.subscribe(callback),
            self.groups.subscribe(callback),
        ]

        def unsubscribe():
            for unsub in unsubscribes:
                unsub()

        return unsubscribe

    async def get_diagnostics(self) -> dict[str, Any]:
        """Return a dict with diagnostic information for debugging and support purposes."""
        result = {}

        # Add raw data of appinfo
        result["appinfo"] = self._app.app_info or ""

        # Add list of IOs
        result["ios"] = self._app.ios or []

        # Add full state to result
        full_state = []
        if len(self.modules) > 0:
            for module in self.modules:
                for io in module.values():
                    full_state.append({"id": io.id, "state": io.state})

        result["full_state"] = full_state

        # Add last event messages to result
        last_events = []
        for item in self._events.last_events:
            last_events.append(item)
        result["events"] = last_events

        return result
