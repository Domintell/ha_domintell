import inspect
from .const import MODULE_TYPE_DICTIONNARY


class BaseModule:
    """Base representation of Domintell module."""

    def __init__(
        self, module_type: str, id: str, sw_version: str | None = None
    ) -> None:
        self._ios: dict = {}  # Listing of IO instances
        self._id: str = id
        self._serial_number: str = id
        self._module_type = module_type  # (ie: "BIR")
        self._model: str | None = MODULE_TYPE_DICTIONNARY[self._module_type]["model"]
        self._module_type_number: str = MODULE_TYPE_DICTIONNARY[self._module_type][
            "mod_type_num"
        ]
        self._software_version: str | None = sw_version  # (ie: "1.0.0")
        self._module_number: int | None = None  # (ie: 10)
        self._io_types: tuple = MODULE_TYPE_DICTIONNARY[self._module_type][
            "io_types_list"
        ]
        self._manufacturer: str = "Domintell"
        self._description: str = MODULE_TYPE_DICTIONNARY[self._module_type][
            "description"
        ]

        # Process module number
        try:
            self._module_number = int(self._serial_number[2:], 16)
        except ValueError:
            self._module_number = None

        # Define module name
        if self._module_type == "SFE":
            # Note: Virtual module DSCENE is not used
            self._name: str = self._model  # (ie: "SCENE")
        else:
            # (ie: "DQG02-253" or "DQG02-253-VIRTUAL")
            self._name: str = self.serial_number_text

    @property
    def id(self) -> str:
        """Id of the module."""
        return self._id

    @property
    def serial_number(self) -> str:
        """Serial number of the module."""
        return self._serial_number

    @property
    def name(self) -> str | None:
        """Name of the module."""
        return self._name

    @property
    def model(self) -> str | None:
        """Model of the module."""
        if self._module_number & (1 << 23):
            return self._model + "-VIRTUAL"

        return self._model

    @property
    def module_type(self) -> str:
        """Type string of the module."""
        return self._module_type

    @property
    def module_type_number(self) -> str:
        """Type number of the module."""
        return self._module_type_number

    @property
    def module_number(self) -> int | None:
        """Number of the module."""
        if self._module_number & (1 << 23):
            # Case of virtual modules
            return (~self._module_number) & 0xFFFFFF

        return self._module_number

    @property
    def serial_number_text(self) -> str | None:
        """Serial Number of the module in text ."""
        sn_text = self._model + "-" + str(self.module_number)

        # Check if module is virtual
        if self._module_number & (1 << 23):
            # Case of virtual modules
            sn_text += "-VIRTUAL"

        return sn_text

    @property
    def software_version(self) -> str:
        """Software version of the module."""
        return self._software_version

    @property
    def manufacturer(self) -> str:
        """Manufacturer of the module."""
        return self._manufacturer

    @property
    def description(self) -> str:
        """Module description."""
        return self._description

    @property
    def io_types(self) -> tuple:
        """List of io types held by the module."""
        return self._io_types

    @property
    def ios(self) -> list:
        """List of IO instances held by the module."""
        return self.values()

    def as_dict(self):
        return {
            k: v
            for k, v in inspect.getmembers(self)
            if not k.startswith("__")
            and not k.startswith("_")
            and not callable(v)
            and k != "ios"
        }

    def _get_io(self, io_type: str, io_offset: str):
        """Get IO by io_type and io_offset."""

        for io in self.ios:
            if io.io_type == io_type and io.io_offset == io_offset:
                return io
        return None

    def _get_io_by_id(self, id: str):
        """Get IO by id."""

        return self._ios.get(id, None)

    def get_io(self, arg1: str, arg2: str | None = None):
        """Get IO by id or by io_type and io_offset."""
        if arg2 is None:
            return self._get_io_by_id(arg1)

        return self._get_io(arg1, arg2)

    def get_ios_by_type(self, io_type: int) -> list:
        my_list = []
        for io_instance in self.ios:
            if io_instance.io_type == io_type:
                my_list.append(io_instance)
        return my_list

    def add_io(self, id: str, io_instance) -> None:
        self._ios[id] = io_instance

    def remove_io(self, id: str) -> None:
        self._ios.pop(id, None)

    def values(self) -> list:
        return list(self._ios.values())

    def keys(self) -> list:
        return list(self._ios.keys())

    def __getitem__(self, id: str):
        return self._ios[id]

    def __iter__(self):
        return iter(self._ios.values())

    def __len__(self):
        return len(self.values())

    def __str__(self):
        return f"""
{self._model}:
  Id: "{self.id}"
  Model: "{self.model}"
  Module Type: "{self.module_type}"
  Module Number: {self.module_number}
  Serial Number: "{self.serial_number}"
  SW Version: "{self.software_version}"
  Manufacturer: "{self.manufacturer}"
  Description: "{self.description}"
"""


class DQGQ02(BaseModule):
    """Representation of Domintell DGQG02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("QG2", id, sw_version)

        # The DQGQ02 module have the following io
        # 12 InputIO
        # 1  TrvIO
        # 8  TorIO
        # 2  Output010VIO
        # 1  AccessControlIO
        # 2  LedIO


class DGQG03(BaseModule):
    """Representation of Domintell DQGQ03 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("QG3", id, sw_version)

        # The DQGQ03 module have the following io


class DQGQ04(BaseModule):
    """Representation of Domintell DQGQ04 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("QG4", id, sw_version)

        # The DGQG04 module have no io


class DQGQ05(BaseModule):
    """Representation of Domintell DQGQ05 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("QG5", id, sw_version)

        # The DQGQ05 module have the following io
        # "io_types_list": ("TypeTorIo", "TypeInputIo", "TypeTrvIo", "TypeLbIo"),


class DNET01(BaseModule):
    """Representation of Domintell DNET01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("NT1", id, sw_version)

        # The DNET01 module have no io


class DNET02(BaseModule):
    """Representation of Domintell DNET02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("NT2", id, sw_version)

        # The DNET02 module have no io


class DLED01(BaseModule):
    """Representation of Domintell DLED01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("LED", id, sw_version)

        # The DLED01 module have the following io
        # 4 LedIO


class DBIR01(BaseModule):
    """Representation of Domintell DBIR01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("BIR", id, sw_version)

        # The DBIR01 module have the following io
        # 8 TorIO


class DMR01(BaseModule):
    """Representation of Domintell DMR01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("DMR", id, sw_version)

        # The DMR01 module have the following io
        # 5 TorIO


class DMR02(BaseModule):
    """Representation of Domintell DMR02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("MR2", id, sw_version)

        # The DMR02 module have the following io
        # 8 TorIO


class DDIM01(BaseModule):
    """Representation of Domintell DDIM01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("DIM", id, sw_version)

        # The DDIM01 module have the following io
        # 8 DimmerIO


class DDIMLV01(BaseModule):
    """Representation of Domintell DDIMLV01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("LV1", id, sw_version)

        # The DDIMLV01 module have the following io
        # N LbIO


class DOUT10V02(BaseModule):
    """Representation of Domintell DOUT10V02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("D10", id, sw_version)

        # The DOUT10V02 module have the following io
        # 1 Out10VIO


class DINTDALI01(BaseModule):
    """Representation of Domintell DINTDALI01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("DAL", id, sw_version)

        # The DINTDALI01 module have the following io
        # Up to 64 DaliIO


class DRGBW01(BaseModule):
    """Representation of Domintell DRGBW01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("RW1", id, sw_version)

        # The DRGBW01 module have the following io
        # 4 DimmerIo or 1 RgbxIo with 4 Channel -> Depends on module configuration


class DDMX01(BaseModule):
    """Representation of Domintell DDMX01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("DMX", id, sw_version)

        # The DDMX01 module have the following io
        # Max 8 DmxIO (8 IO with 1 channel or 1 IO with 8 channels)


class DDMX02(BaseModule):
    """Representation of Domintell DDMX02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("DX2", id, sw_version)

        # The DDMX02 module have the following io
        # Max 8 DmxIO (8 IO with 1 channel or 1 IO with 8 channels)


class DTRP01(BaseModule):
    """Representation of Domintell DTRP01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("TRP", id, sw_version)

        # The DTRP01 module have the following io
        # 4 TorIO


class DTRP02(BaseModule):
    """Representation of Domintell DTRP02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("TPV", id, sw_version)

        # The DTRP02 module have the following io
        # 2 TrvIO


class DTRVBT01(BaseModule):
    """Representation of Domintell DTRVBT01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("V24", id, sw_version)

        # The DTRVBT01 module have the following io
        # 1 TrvBtIO


class DTRV01(BaseModule):
    """Representation of Domintell DTRV01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("TRV", id, sw_version)

        # The DTRV01 module have the following io
        # 4 TrvIO


class DISM04(BaseModule):
    """Representation of Domintell DISM04 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("IS4", id, sw_version)

        # The DISM04 module have the following io
        # 4 InputIO


class DISM08(BaseModule):
    """Representation of Domintell DISM08 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("IS8", id, sw_version)

        # The DISM08 module have the following io
        # 8 InputIO


class DISM20(BaseModule):
    """Representation of Domintell DISM20 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("I20", id, sw_version)

        # The DISM20 module have the following io
        # 20 InputIO


class DIN10V02(BaseModule):
    """Representation of Domintell DIN10V02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("I10", id, sw_version)

        # The DIN10V02 module have the following io
        # 1 In10VIO


class DPBx01(BaseModule):
    """Representation of Domintell DPBx01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("BU1", id, sw_version)

        # The DPBx01 module have the following io
        # 1 InputIO
        # 1 LedIO


class DPBx02(BaseModule):
    """Representation of Domintell DPBx02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("BU2", id, sw_version)

        # The DPBx02 module have the following io
        # 2 InputIO
        # 2 LedIO


class DPBx04(BaseModule):
    """Representation of Domintell DPBx04 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("BU4", id, sw_version)

        # The DPBx04 module have the following io
        # 4 InputIO
        # 4 LedIO


class DPBx06(BaseModule):
    """Representation of Domintell DPBx06 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("BU6", id, sw_version)

        # The DPBx06 module have the following io
        # 6 InputIO
        # 6 LedIO


class DPBTLCD0x(BaseModule):
    """Representation of Domintell DPBTLCD0x module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("PBL", id, sw_version)

        # The DPBTLCD0x module have the following io
        # Up to 6 InputIO
        # Up to 1 SensorIO (for odd serial number only)
        # Up to 6 LedIO


class DPBR02(BaseModule):
    """Representation of Domintell DPBR02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("BR2", id, sw_version)

        # The DPBR02 module have the following io
        # 2 InputIO
        # 2 RgbwIO


class DPBR04(BaseModule):
    """Representation of Domintell DPBR04 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("BR4", id, sw_version)

        # The DPBR04 module have the following io
        # 4 InputIO
        # 4 RgbwIO


class DPBRLCD02(BaseModule):
    """Representation of Domintell DPBRLCD02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("PRL", id, sw_version)

        # The DPBRLCD02 module have the following io
        # 6 InputIO
        # 1 SensorIO


class DPBL01(BaseModule):
    """Representation of Domintell DPBL01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("B81", id, sw_version)

        # The DPBL01 module have the following io
        # 1 InputIO
        # 1 Led8cIo


class DPBL02(BaseModule):
    """Representation of Domintell DPBL02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("B82", id, sw_version)

        # The DPBL02 module have the following io
        # 2 InputIO
        # 2 Led8cIo


class DPBL04(BaseModule):
    """Representation of Domintell DPBL04 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("B84", id, sw_version)

        # The DPBL04 module have the following io
        # 4 InputIO
        # 4 Led8cIo


class DPBR06(BaseModule):
    """Representation of Domintell DPBR06 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("B84", id, sw_version)

        # The DPBR06 module have the following io
        # 6 InputIO
        # 6 LedRgbIo


class DPBC01(BaseModule):
    """Representation of Domintell DPBC01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("CL1", id, sw_version)

        # The DPBC01 module have the following io
        # 1 InputIO
        # 1 Led8cIo
        # 1 SensorIO


class DPBC02(BaseModule):
    """Representation of Domintell DPBC02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("CL2", id, sw_version)

        # The DPBC02 module have the following io
        # 2 InputIO
        # 2 Led8cIo
        # 1 SensorIO


class DPBC04(BaseModule):
    """Representation of Domintell DPBC04 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("CL4", id, sw_version)

        # The DPBC04 module have the following io
        # 4 InputIO
        # 4 Led8cIo
        # 1 SensorIO


class DPBC06(BaseModule):
    """Representation of Domintell DPBC06 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("CL6", id, sw_version)

        # The DPBC06 module have the following io
        # 6 InputIO
        # 6 Led8cIo
        # 1 SensorIO


class DPBRT0x(BaseModule):
    """Representation of Domintell DPBRT0x module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("BRT", id, sw_version)

        # The DPBRT0x module have the following io
        # up to 6 InputIO
        # 1 SensorIO
        # up to 6 LedRgbIo


class DTSC02(BaseModule):
    """Representation of Domintell DTSC02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("LT2", id, sw_version)

        # The DTSC02 module have the following io
        # 4 InputIo
        # 1 SensorIo
        # 1 IrIO
        # 4 LedIO


class DTSC04(BaseModule):
    """Representation of Domintell DTSC04 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("LT4", id, sw_version)

        # The DTSC04 module have the following io
        # 4 InputIo
        # 1 SensorIo
        # 1 IrIO
        # 4 LedIO


class DTSC05(BaseModule):
    """Representation of Domintell DTSC05 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("LT5", id, sw_version)

        # The DTSC05 module have the following io
        # 4 InputIo
        # 4 LedIo
        # 1 SensorIo
        # 1 VideoIo
        # 1 HumidityIo
        # 1 GestureIO


class DTEM01(BaseModule):
    """Representation of Domintell DTEM01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("TE1", id, sw_version)

        # The DTEM01 module have the following io
        # 1 SensorIO


class DTEM02(BaseModule):
    """Representation of Domintell DTEM02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("TE2", id, sw_version)

        # The DTEM02 module have the following io
        # 1 SensorIO


class DMOV0x(BaseModule):
    """Representation of Domintell DMOV01/02/05 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("DET", id, sw_version)

        # The DMOV0x module have the following io
        # 1 MovIO


class DMOV06(BaseModule):
    """Representation of Domintell DMOV06 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("MV6", id, sw_version)

        # The DMOV06 module have the following io
        # 1 MovIO
        # 1 LuxIO


class DMOV07(BaseModule):
    """Representation of Domintell DMOV07 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("MV7", id, sw_version)

        # The DMOV07 module have the following io
        # 1 MovIO
        # 1 LuxIO


class DWIND01(BaseModule):
    """Representation of Domintell DWIND01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("WI1", id, sw_version)

        # The DWIND01 module have the following io
        # 1 WindIO


class DENV01(BaseModule):
    """Representation of Domintell DENV01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("EV1", id, sw_version)

        # The DENV01 module have the following io
        # 1 SensorIO
        # 1 LuxIo
        # 1 HumidityIo
        # 1 PressureIo


class DENV02(BaseModule):
    """Representation of Domintell DENV02 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("EV2", id, sw_version)

        # The DENV02 module have the following io
        # 1 SensorIO
        # 1 HumidityIo
        # 1 Co2Io


class DALI04(BaseModule):
    """Representation of Domintell DALI04 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("PS4", id, sw_version)

        # The DALI04 module have the following io
        # 1 PowerSupplyIO


class DALI05(BaseModule):
    """Representation of Domintell DALI05 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("PS5", id, sw_version)

        # The DALI05 module have the following io
        # 1 PowerSupplyIO


class DPBRTHERM01(BaseModule):
    """Representation of Domintell DPBRTHERM01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("RT1", id, sw_version)

        # The DPBRTHERM01 module have the following io
        # 1 SensorIO


class DMONOELEC01(BaseModule):
    """Representation of Domintell DMONOELEC01 device."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("MON", id, sw_version)

        # The DMONOELEC01 module have the following io
        # 1 ElecIO


class DTRIELEC01(BaseModule):
    """Representation of Domintell DTRIELEC01 device."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("TRI", id, sw_version)

        # The DTRIELEC01 module have the following io
        # 1 ElecIO


class DELEC01(BaseModule):
    """Representation of Domintell DELEC01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("EL1", id, sw_version)

        # The DELEC01 module have the following io
        # 1 ElecIO


class DMV01(BaseModule):
    """Representation of Domintell DMV01 virtual module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("DMV", id, sw_version)

        # The DMV01 module have the following io
        # 1 FanIO
        # 2 TorIO


class DFAN01(BaseModule):
    """Representation of Domintell DFAN01 virtual module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("FAN", id, sw_version)

        # The DFAN01 module have the following io
        # 1 DfanComboIO


class DOORSTATION(BaseModule):
    """Representation of Domintell DOORSTATION virtual module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("DST", id, sw_version)

        # The DOORSTATION module have the following io
        # 1 InputIO (Virtual unlock door push-button)
        # 1 MovIO (Motion Detector)
        # N TorBasicTempoIO (Relays)
        # N InputTriggerIO (Calling push-buton)


class DDIR0x(BaseModule):
    """Representation of Domintell DDIR01 and DDIR02 virtual module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("DIR", id, sw_version)

        # The DDIR0x module have the following io
        # 1 IrIO


class DAMPLI01(BaseModule):
    """Representation of Domintell DAMPLI01 module."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("AMP", id, sw_version)

        # The DAMPLI01 module have the following io
        # Up to 4 SoundIo


class DMODBUS(BaseModule):
    """Representation of Domintell Modbus generic device."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("MBG", id, sw_version)

        # The DMODBUS module have the following io
        # Depends on the connected modbus device


class DAIRCO(BaseModule):
    """Representation of Domintell Modbus Air conditioner device."""

    def __init__(self, id: str, sw_version: str | None = None) -> None:
        super().__init__("MBA", id, sw_version)

        # The DAIRCO module have the following io
        # Depends on the connected modbus device


class ModuleFactory:
    """Generic representation of a Domintell module."""

    def __init__(self):
        self._module_classes: dict = {
            "QG2": DQGQ02,
            "QG3": DGQG03,
            "QG4": DQGQ04,
            "QG5": DQGQ05,
            "NT1": DNET01,
            "NT2": DNET02,
            "LED": DLED01,
            "BIR": DBIR01,
            "DMR": DMR01,
            "MR2": DMR02,
            "DIM": DDIM01,
            "LV1": DDIMLV01,
            "D10": DOUT10V02,
            "DAL": DINTDALI01,
            "RW1": DRGBW01,
            "DMX": DDMX01,
            "DX2": DDMX02,
            "TRP": DTRP01,
            "TPV": DTRP02,
            "V24": DTRVBT01,
            "TRV": DTRV01,
            "IS4": DISM04,
            "IS8": DISM08,
            "I20": DISM20,
            "I10": DIN10V02,
            "BU1": DPBx01,
            "BU2": DPBx02,
            "BU4": DPBx04,
            "BU6": DPBx06,
            "PBL": DPBTLCD0x,
            "BR2": DPBR02,
            "BR4": DPBR04,
            "PRL": DPBRLCD02,
            "B81": DPBL01,
            "B82": DPBL02,
            "B84": DPBL04,
            "BR6": DPBR06,
            "CL1": DPBC01,
            "CL2": DPBC02,
            "CL4": DPBC04,
            "CL6": DPBC06,
            "BRT": DPBRT0x,
            "LT2": DTSC02,
            "LT4": DTSC04,
            "LT5": DTSC05,
            "TE1": DTEM01,
            "TE2": DTEM02,
            "DET": DMOV0x,
            "MV6": DMOV06,
            "MV7": DMOV07,
            "WI1": DWIND01,
            "EV1": DENV01,
            "EV2": DENV02,
            "PS4": DALI04,
            "PS5": DALI05,
            "RT1": DPBRTHERM01,
            "MON": DMONOELEC01,
            "TRI": DTRIELEC01,
            "EL1": DELEC01,
            "DMV": DMV01,
            "FAN": DFAN01,
            "DST": DOORSTATION,
            "DIR": DDIR0x,
            "AMP": DAMPLI01,
            "MBG": DMODBUS,  # ModBus generic device
            "MBA": DAIRCO,  # Air conditioner device
        }

    def create_module(self, module_type: str, **kwargs):
        if module_type in self._module_classes:
            return self._module_classes[module_type](**kwargs)
        else:
            raise ValueError(f"Unknown Module type: {module_type}")
