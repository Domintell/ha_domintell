from .base import BaseController
from .events import EventType, ResourceTypes

from ..modules import ModuleFactory
from ..iotypes import IOFactory
from ..const import (
    NOT_A_MODULE_TYPE_LIST,
    MODULE_TYPE_OF_MODULES_WITH_NO_IO,
    MASTER_MODULE_TYPE_LIST,
    DNET_MODULE_TYPE_LIST,
    GATEWAY_MODULE_TYPE_LIST,
    IO_TYPES_STRING,
    MODULE_TYPE_DICTIONNARY,
    get_module_type_by_model,
)


ID_FILTER_ALL = "*"


class ModulesController(BaseController):
    """Controller holding and managing Domintell resources of type 'module'."""

    item_type = ResourceTypes.MODULE

    def __init__(self, gateway) -> None:
        """Initialize instance."""
        super().__init__(gateway)
        self._initialized = False

    def get_module(self, id: str):
        """Get module by id."""
        # ie: module_id -> (module SN) "520000FD"

        return self._items.get(id, None)

    def get_modules_master(self):
        """Return list of modules Master."""

        master_list: list = []
        for module in self._items.values():
            if module.module_type in MASTER_MODULE_TYPE_LIST:
                master_list.append(module)

        return master_list

    def get_modules_dnet(self):
        """Return list of modules DNET0x."""

        dnet_list: list = []
        for module in self._items.values():
            if module.module_type in DNET_MODULE_TYPE_LIST:
                dnet_list.append(module)

        return dnet_list

    def get_modules_without_ios(self):
        """Returns the list of module that have no IOs."""
        modules_list = [module for module in self.values() if len(module.values()) == 0]
        return modules_list

    def get_io(self, id: str):
        """Get IO by id."""

        module_type = id[:3]
        if module_type not in NOT_A_MODULE_TYPE_LIST:
            # ie:  io_id -> "QG20000FD-1-8" convert to module_id (module SN) "520000FD"
            module_type_num = MODULE_TYPE_DICTIONNARY.get(module_type)["mod_type_num"]
            module_id = module_type_num + id[3:9]
        else:
            # For io attached to the gateway, you should not rely on the construction of the module_id
            module_id = None
            for module in self._items.values():
                for io in module:
                    if io.id == id:
                        module_id = module.id
                        break
                if module_id is not None:
                    break

        module = self.get_module(module_id)

        if module is None:
            return None

        return module.get_io(id)

    def get_module_of_io(self, io_id: str):
        """Get the module of an IO by io_id."""

        module_type = io_id[:3]
        module_id = None
        if module_type not in NOT_A_MODULE_TYPE_LIST:
            # ie:  io_id -> "QG20000FD-1-8" convert to module_id (module SN) "520000FD"
            module_type_num = MODULE_TYPE_DICTIONNARY.get(module_type)["mod_type_num"]
            module_id = module_type_num + io_id[3:9]
        else:
            # For io attached to the gateway, you should not rely on the construction of the module_id
            for module in self._items.values():
                for io in module:
                    if io.id == io_id:
                        module_id = module.id
                        break
                if module_id is not None:
                    break

        if module_id is not None:
            return self.get_module(module_id)
        return None

    def _create_module_instances(self, ios):
        """Create instances of modules and their IOs"""
        instances = []
        seen_modules = set()  # To keep track of modules already encountered
        deferred_ios = []  # VAR/SYS/SFE/MEM IOs deferred until gateway is available

        # Retrieve all instances of existing modules
        existing_modules = self.values()
        for module in existing_modules:
            instances.append(module)
            seen_modules.add(module.serial_number)

        # --- Pass 1: Create all hardware modules and assign their IOs ---
        for element in ios:
            module_type = element["module_type"]
            module_sn = element["serial_number"]  # Serial number of the io module

            # Defer IOs that belong to the gateway (VAR/SYS/SFE/MEM)
            if module_type in NOT_A_MODULE_TYPE_LIST:
                deferred_ios.append(element)
                continue

            # Create and add module instance
            if module_sn not in seen_modules:
                seen_modules.add(module_sn)

                # Create a module instance with the element data
                module_data = {
                    "id": element["serial_number"],
                    "sw_version": element["sw_version"],
                }

                instance = ModuleFactory().create_module(module_type, **module_data)
                instances.append(instance)

            # Find the module instance that should contain the io
            instance_of_module_io = next(
                (
                    instance
                    for instance in instances
                    if instance.serial_number == module_sn
                ),
                None,
            )

            # Create and add io instance in module instance
            if instance_of_module_io is not None:
                self._add_io_to_module(instance_of_module_io, element)

        # --- Ensure a gateway module exists for deferred IOs ---
        gateway_module = next(
            (
                m
                for m in instances
                if m.module_type in GATEWAY_MODULE_TYPE_LIST
            ),
            None,
        )

        # If no gateway module was found in appinfo IOs, create one from
        # gateway_info (config entry identity, or WebSocket discovery fallback).
        if gateway_module is None:
            gw_info = self._gateway.gateway_info
            if gw_info is not None:
                gw_model = gw_info.get("model", "")
                gw_type = get_module_type_by_model(gw_model)
                if gw_type is not None:
                    try:
                        gateway_module = ModuleFactory().create_module(
                            gw_type, id=gw_info["id"], sw_version=None
                        )
                        instances.append(gateway_module)
                        seen_modules.add(gateway_module.serial_number)
                        self._logger.debug(
                            "Created gateway module %s (%s) from gateway info",
                            gw_info["id"],
                            gw_type,
                        )
                    except ValueError:
                        self._logger.warning(
                            "Gateway type '%s' not supported by ModuleFactory",
                            gw_type,
                        )
                else:
                    self._logger.warning(
                        "Unknown gateway model '%s' from gateway info",
                        gw_model,
                    )
            else:
                self._logger.warning(
                    "No gateway module in appinfo and no gateway info available; "
                    "%d IOs (VAR/SYS/SFE/MEM) will not be assigned",
                    len(deferred_ios),
                )

        # --- Pass 2: Assign deferred IOs (VAR/SYS/SFE/MEM) to gateway ---
        if gateway_module is not None and deferred_ios:
            for element in deferred_ios:
                self._add_io_to_module(gateway_module, element)
        elif gateway_module is None and deferred_ios:
            self._logger.warning(
                "Dropping %d IOs (VAR/SYS/SFE/MEM) — no gateway module available",
                len(deferred_ios),
            )

        # Remove modules that were already present
        instances_to_keep = [
            module for module in instances if module not in existing_modules
        ]

        return instances_to_keep

    def _add_io_to_module(self, module, element):
        """Create an IO instance and add it to the given module."""
        module_type = element["module_type"]

        if (
            (module_type in MODULE_TYPE_OF_MODULES_WITH_NO_IO)
            and element["io_type"] == 0
            and element["io_offset"] == 0
        ):
            # Placeholder IO from modules with no real IOs — skip
            return

        io_type_string = IO_TYPES_STRING.get(element["io_type"], 0)

        if (
            io_type_string in module.io_types
            or module.module_type in GATEWAY_MODULE_TYPE_LIST
        ):
            instance_of_io = IOFactory().create_io(
                io_type_string, self._gateway, **element
            )
            module.add_io(element["id"], instance_of_io)

    async def initialize(self, ios: dict):  # pylint: disable=W0221
        """Initialize modules list."""
        modules = self._create_module_instances(ios)

        # Add each module in controller
        for module in modules:
            await self._handle_event(
                EventType.RESOURCE_ADDED, {"id": module.id, "instance": module}
            )

        self._logger.debug("fetched %s modules", len(modules))

        # Subscribe to module events
        self._gateway.events.subscribe(
            self._handle_event, resource_filter=self.item_type
        )

        self._initialized = True

    async def update(self, ios_removed, ios_added):
        """Update modules list."""

        def delete_ios(modules, ios_to_delete) -> None:
            ids_to_delete = [io["id"] for io in ios_to_delete]
            for module in modules.items:
                for io in module.ios:
                    for io_id in ids_to_delete:
                        if io.id == io_id:
                            module.remove_io(io_id)

        # Remove modules
        if ios_removed is not None:
            delete_ios(self, ios_removed)
            modules_empty = self.get_modules_without_ios()

            # Remove gateway module from the list if present
            for i, module in enumerate(modules_empty):
                if module.id == self._gateway.gateway_id:
                    del modules_empty[i]

            for module in modules_empty:
                await self._handle_event(EventType.RESOURCE_DELETED, {"id": module.id})

        # Add new modules and their ios
        if ios_added is not None:
            new_modules = self._create_module_instances(ios_added)
            for module in new_modules:
                await self._handle_event(
                    EventType.RESOURCE_ADDED, {"id": module.id, "instance": module}
                )

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""

        await super()._handle_event(event_type, event_data)
