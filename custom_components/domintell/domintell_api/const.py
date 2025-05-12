UNSUPPORTED_MODULE_TYPE_LIST = (
    "LCD",  # DLCD01
    "LC3",  # DLCD03
    "T35",  # DTSC35
    "TSB",  # DTSC01/03
    "VI1",  # DVIP01
    "VI2",  # DVIP02
    "DLB",  # DLB01 not addressable directly
    "MB1",  # DINTMB01 Deprecated ModBus interface
    "MBD",  # MBDEV01  For Daikin RTD-NET (deprecated)
    "ACD",  # DINTMB02 (deprecated module_type for this module)
    "ET2",  # DETH02
    "RS2",  # DRS23202
    "CLK",  # CLOCK
)

SUPPORTED_MODULE_TYPE_LIST = (
    "QG1"  # DGQG01 Gen 1 Master (with module DNET01)
    "DIR",  # DDIR01, DDIR02
    "IS8",  # DISM08
    "BU1",  # DPB(U/T)01
    "BU2",  # DPB(U/T)02
    "BU4",  # DPB(U/T)04
    "BU6",  # DPB(U/T)06
    "BIR",  # DBIR01
    "TRV",  # DTRV01
    "TRP",  # DTRP01
    "DIM",  # DDIM01
    "TE1",  # DTEM01
    "TE2",  # DTEM02
    "LED",  # DLED01
    "IS4",  # DISM04
    "DMV",  # DMV01
    "DET",  # DMOV01, DMOV02, DMOV05
    "V24",  # DTRVBT01
    "I10",  # DIN10V02
    "TPV",  # DTRP02
    # "AMP",  # DAMPLI01 TODO For now
    "D10",  # DOUT10V02
    "PBL",  # DPBTLCD0x
    "FAN",  # DFAN01
    "DMR",  # DMR01
    "PRL",  # DPBRLCD02
    "BR2",  # DPBR02
    "MON",  # DMONOELEC01
    "TRI",  # DTRIELEC01
    "LT2",  # DTSC02
    # "DMX",  # DMX01 #TODO For now
    "LT4",  # DTSC04
    "BR4",  # DPBR04
    "DAL",  # DINTDALI01
    "B81",  # DPBL01
    "B82",  # DPBL02
    "B84",  # DPBL04
    "B86",  # DPBL06
    "BR6",  # DPBR06
    "I20",  # DISM20
    "WI1",  # DWIND01
    "DX2",  # DDMX02
    "CL1",  # DPBC01
    "CL2",  # DPBC02
    "CL4",  # DPBC04
    "CL6",  # DPBC06
    "QG2",  # DGQG02
    "QG3",  # DGQG03
    "QG4",  # DGQG04
    "LT5",  # DTSC05
    "EV1",  # DENV01
    "EV2",  # DENV02
    "MV6",  # DMOV06
    "LV1",  # DDIMLV01
    "RW1",  # DRGBW01
    "PS4",  # DALI04
    "PS5",  # DALI05
    "NT1",  # DNET01
    "NT2",  # DNET02
    "BRT",  # DPBRT0x
    "MV7",  # DMOV07
    "RT1",  # DPBRTHERM01
    "QG5",  # DGQG05
    "EL1",  # DELEC01
    "MR2",  # DMR02
    # "MB2",  # DINTMB02 #TODO
    "MBG",  # ModBus generic device
    "MBA",  # Air conditioner device
    "DST",  # DOORSTATION
    "SFE",  # SCENE
    "SYS",  # SYSVAR
    "VAR",  # VAR
    "MEM",  # GROUP
)

SUPPORTED_IO_TYPE_LIST = (
    0,  # "TypeIoNotHandled"
    1,  # "TypeTorIo"
    2,  # "TypeInputIo"
    3,  # "TypeDimmerIo"
    # 4, #"TypeStringInputIo"
    # 5, #"TypeStringOutputIo"
    6,  # "TypeTrvIo"
    7,  # "TypeTrvBtIo"
    8,  # "TypeSensorIo"
    9,  # "TypeIrIo"
    10,  # "TypeLedIo"
    # 11, #"TypeDummyIo" (never in LP)
    12,  # "TypeDfanComboIo"
    13,  # "TypeFanIo"
    # 14, #"TypeCamIo"
    15,  # "TypeLed8cIo"
    16,  # "TypeVar"
    17,  # "TypeVarSys"
    # 18, #"TypeSoundIo" #TODO For now
    # 19, #"TypeIrEmitIo"
    20,  # "TypePbLcdIo"
    21,  # "TypeIn10VIo"
    # 22, #"TypeSingleInput"
    23,  # "TypeOut10VIo"
    24,  # "TypeElecIo"
    25,  # "TypeDmxIo"
    # 26, #"TypePulseIo"
    # 27, #"TypeCombinationPulseIo"
    # 28, #"TypeVipDisplay"
    29,  # "TypeDali"
    # 30, #"TypeRtdNetIo"
    31,  # "TypeVideoIo"
    # 32, #"TypeGsmInputIo"
    # 33, #"TypeGsmOutputIo"
    34,  # "TypeMovIo"
    35,  # "TypeOut10VIo255"
    36,  # "TypeLuxIo"
    37,  # "TypeHumidityIo"
    38,  # "TypePressureIo"
    39,  # "TypeCo2Io"
    40,  # "TypeAccessControlIo"
    41,  # "TypeWindIo"
    42,  # "TypeLbIo"
    43,  # "TypeGenericSoundIo"
    # 44, #"TypeCoolMasterIo" (obsolete)
    # 45, #"TypeClock"
    46,  # "TypeRgbwIo"
    # 47, # "TypeTunableWhite"
    # 48, #"TypeNetworkTextIo"
    49,  # "TypeGestureIo"
    # 50, # "TypeTempProfile"
    51,  # "TypePowerSupplyIo"
    52,  # "TypeTorBasicTempoIo"
    53,  # "TypeInputTriggerIo"
    54,  # "TypeVanesIo" (formerly TypeSwingIo)
    55,  # "TypeDeviceStatus"
    56,  # "TypePercentInIo"
    57,  # "TypeAnalogInIo"
    # 58, # "TypeAccessControlCardItem"
    # 59, # "TypeLink" (never in LP)
    60,  # "TypeLedRgbIo"
    # 61, #"TypeCloudNotif" (probably never in LP)
    62,  # "TypeCloudInfo"
    63,  # "TypeEthernetInfo"
    64,  # "TypeMemoryInfo"
    65,  # "TypeStorageInfo"
    66,  # "TypeCpuInfo"
    67,  # "TypeDiBusGwInfo"
)


IO_TYPES_STRING: dict[int, str] = {
    0: "TypeIoNotHandled",
    1: "TypeTorIo",
    2: "TypeInputIo",
    3: "TypeDimmerIo",
    4: "TypeStringInputIo",
    5: "TypeStringOutputIo",
    6: "TypeTrvIo",
    7: "TypeTrvBtIo",
    8: "TypeSensorIo",
    9: "TypeIrIo",
    10: "TypeLedIo",
    11: "TypeDummyIo",
    12: "TypeDfanComboIo",
    13: "TypeFanIo",
    14: "TypeCamIo",
    15: "TypeLed8cIo",
    16: "TypeVar",
    17: "TypeVarSys",
    18: "TypeSoundIo",
    19: "TypeIrEmitIo",
    20: "TypePbLcdIo",
    21: "TypeIn10VIo",
    22: "TypeSingleInput",
    23: "TypeOut10VIo",
    24: "TypeElecIo",
    25: "TypeDmxIo",
    26: "TypePulseIo",
    27: "TypeCombinationPulseIo",
    28: "TypeVipDisplay",
    29: "TypeDali",
    30: "TypeRtdNetIo",
    31: "TypeVideoIo",
    32: "TypeGsmInputIo",
    33: "TypeGsmOutputIo",
    34: "TypeMovIo",
    35: "TypeOut10VIo255",
    36: "TypeLuxIo",
    37: "TypeHumidityIo",
    38: "TypePressureIo",
    39: "TypeCo2Io",
    40: "TypeAccessControlIo",
    41: "TypeWindIo",
    42: "TypeLbIo",
    43: "TypeGenericSoundIo",
    44: "TypeCoolMasterIo",
    45: "TypeClock",
    46: "TypeRgbwIo",
    47: "TypeTunableWhite",
    48: "TypeNetworkTextIo",
    49: "TypeGestureIo",
    50: "TypeTempProfile",
    51: "TypePowerSupplyIo",
    52: "TypeTorBasicTempoIo",
    53: "TypeInputTriggerIo",
    54: "TypeVanesIo",  # (formerly TypeSwingIo)
    55: "TypeDeviceStatus",
    56: "TypePercentInIo",
    57: "TypeAnalogInIo",
    58: "TypeAccessControlCardItem",
    59: "TypeLink",
    60: "TypeLedRgbIo",
    61: "TypeCloudNotif",
    62: "TypeCloudInfo",
    63: "TypeEthernetInfo",
    64: "TypeMemoryInfo",
    65: "TypeStorageInfo",
    66: "TypeCpuInfo",
    67: "TypeDiBusGwInfo",
}

IO_TYPES_INT: dict[str, int] = {
    "TypeIoNotHandled": 0,
    "TypeTorIo": 1,
    "TypeInputIo": 2,
    "TypeDimmerIo": 3,
    "TypeStringInputIo": 4,
    "TypeStringOutputIo": 5,
    "TypeTrvIo": 6,
    "TypeTrvBtIo": 7,
    "TypeSensorIo": 8,
    "TypeIrIo": 9,
    "TypeLedIo": 10,
    "TypeDummyIo": 11,
    "TypeDfanComboIo": 12,
    "TypeFanIo": 13,
    "TypeCamIo": 14,
    "TypeLed8cIo": 15,
    "TypeVar": 16,
    "TypeVarSys": 17,
    "TypeSoundIo": 18,
    "TypeIrEmitIo": 19,
    "TypePbLcdIo": 20,
    "TypeIn10VIo": 21,
    "TypeSingleInput": 22,
    "TypeOut10VIo": 23,
    "TypeElecIo": 24,
    "TypeDmxIo": 25,
    "TypePulseIo": 26,
    "TypeCombinationPulseIo": 27,
    "TypeVipDisplay": 28,
    "TypeDali": 29,
    "TypeRtdNetIo": 30,
    "TypeVideoIo": 31,
    "TypeGsmInputIo": 32,
    "TypeGsmOutputIo": 33,
    "TypeMovIo": 34,
    "TypeOut10VIo255": 35,
    "TypeLuxIo": 36,
    "TypeHumidityIo": 37,
    "TypePressureIo": 38,
    "TypeCo2Io": 39,
    "TypeAccessControlIo": 40,
    "TypeWindIo": 41,
    "TypeLbIo": 42,
    "TypeGenericSoundIo": 43,
    "TypeCoolMasterIo": 44,
    "TypeClock": 45,
    "TypeRgbwIo": 46,
    "TypeTunableWhite": 47,
    "TypeNetworkTextIo": 48,
    "TypeGestureIo": 49,
    "TypeTempProfile": 50,
    "TypePowerSupplyIo": 51,
    "TypeTorBasicTempoIo": 52,
    "TypeInputTriggerIo": 53,
    "TypeVanesIo": 54,  # (formerly TypeSwingIo)
    "TypeDeviceStatus": 55,
    "TypePercentInIo": 56,
    "TypeAnalogInIo": 57,
    "TypeAccessControlCardItem": 58,
    "TypeLink": 59,
    "TypeLedRgbIo": 60,
    "TypeCloudNotif": 61,
    "TypeCloudInfo": 62,
    "TypeEthernetInfo": 63,
    "TypeMemoryInfo": 64,
    "TypeStorageInfo": 65,
    "TypeCpuInfo": 66,
    "TypeDiBusGwInfo": 67,
}


LEGACY_MODULE_TYPE_LIST = (
    "QG1",  # DGQG01
    "NT1",  # DNET01
    "NT2",  # DNET02
    "IS8",  # DISM08
    "BU1",  # DPB(U/T)01
    "BU2",  # DPB(U/T)02
    "BU4",  # DPB(U/T)04
    "BU6",  # DPB(U/T)06
    "BIR",  # DBIR01
    "TRV",  # DTRV01
    "TRP",  # DTRP01
    "DIM",  # DDIM01
    "TE1",  # DTEM01
    "TE2",  # DTEM02
    "LCD",  # DLCD01
    "DIR",  # DDIR01, DDIR02
    "LED",  # DLED01
    "IS4",  # DISM04
    "TSB",  # DTSC01/03
    "DMV",  # DMV01
    "DET",  # DMOV01, DMOV02, DMOV05
    "V24",  # DTRVBT01
    "I10",  # DIN10V02
    "LC3",  # DLCD03
    "TPV",  # DTRP02
    "AMP",  # DAMPLI01
    "D10",  # DOUT10V02
    "PBL",  # DPBTLCD0x
    "FAN",  # DFAN01
    "DMR",  # DMR01
    "PRL",  # DPBRLCD02
    "BR2",  # DPBR02
    "ET2",  # DRS23202
    "LT2",  # DTSC02
    "DMX",  # DMX01
    "LT4",  # DTSC04
    "T35",  # DTSC35
    "VI1",  # DVIP01
    "BR4",  # DPBR04
    "VI2",  # DVIP02
    "DAL",  # DINTDALI01
    "B81",  # DPBL01
    "B82",  # DPBL02
    "B84",  # DPBL04
    "B86",  # DPBL06
    "BR6",  # DPBR06
    "I20",  # DISM20
    "MBD",  # MBDEV01
    "CL1",  # DPBC01
    "CL2",  # DPBC02
    "CL4",  # DPBC04
    "CL6",  # DPBC06
    "DLB",  # DLB01
    "CLK",  # CLOCK
    "SFE",  # SCENE
    "MEM",  # GROUP
    "SYS",  # SYSVAR
    "VAR",  # VAR
    "CAM",  # CAM
)

IO_DEFAULT_TARGET_TYPES: dict = {
    0: "scene",  # "TypeIoNotHandled"
    1: "switch",  # "TypeTorIo"
    2: "button",  # "TypeInputIo"  # TODO or binary_sensor
    3: "light",  # "TypeDimmerIo"
    4: "unknown",  # "TypeStringInputIo"
    5: "unknown",  # "TypeStringOutputIo"
    6: "cover",  # "TypeTrvIo"
    7: "cover",  # "TypeTrvBtIo"
    8: "temperature",  # "TypeSensorIo"
    9: "button",  # "TypeIrIo"
    10: "light",  #  "TypeLedIo"
    11: "unknown",  # "TypeDummyIo"  (never in LP)
    12: "fan",  # "TypeDfanComboIo"
    13: "fan",  # "TypeFanIo"
    14: "unknown",  # "TypeCamIo"
    15: "light",  # "TypeLed8cIo"
    16: "variable",  # "TypeVar"
    17: "variable",  # "TypeVarSys"
    18: "unknown",  # "TypeSoundIo"
    19: "unknown",  # "TypeIrEmitIo"
    20: "light",  # "TypePbLcdIo"
    21: "analog",  # "TypeIn10VIo"
    22: "unknown",  # "TypeSingleInput"
    23: "light",  # "TypeOut10VIo"
    24: "electricity",  # "TypeElecIo"
    25: "light",  # "TypeDmxIo"
    26: "unknown",  # "TypePulseIo"
    27: "unknown",  # "TypeCombinationPulseIo"
    28: "unknown",  # "TypeVipDisplay"
    29: "light",  # "TypeDali"
    30: "unknown",  # "TypeRtdNetIo"
    31: "unknown",  # "TypeVideoIo"
    32: "unknown",  # "TypeGsmInputIo"
    33: "unknown",  # "TypeGsmOutputIo"
    34: "motion",  # "TypeMovIo"
    35: "light",  # "TypeOut10VIo255"
    36: "illuminance",  # "TypeLuxIo"
    37: "humidity",  # "TypeHumidityIo"
    38: "pressure",  # "TypePressureIo"
    39: "carbon_dioxide",  # "TypeCo2Io"
    40: "unknown",  # "TypeAccessControlIo"
    41: "wind",  # "TypeWindIo"
    42: "light",  # "TypeLbIo"
    43: "unknown",  # "TypeGenericSoundIo"
    44: "unknown",  # "TypeCoolMasterIo"
    45: "unknown",  # "TypeClock"
    46: "light",  # "TypeRgbwIo"
    47: "light",  # "TypeTunableWhite"
    48: "unknown",  # "TypeNetworkTextIo"
    49: "button",  # "TypeGestureIo"
    50: "unknown",  # "TypeTempProfile"
    51: "power_supply",  # "TypePowerSupplyIo"
    52: "momentary_switch",  # "TypeTorBasicTempoIo"
    53: "button",  # "TypeInputTriggerIo"
    54: "unknown",  # "TypeVanesIo" # (formerly TypeSwingIo) # TODO climate
    55: "unknown",  # "TypeDeviceStatus"
    56: "sensor",  # "TypePercentInIo"
    57: "sensor",  # "TypeAnalogInIo"
    58: "unknown",  # "TypeAccessControlCardItem"
    59: "unknown",  # "TypeLink" (never in LP)
    60: "light",  # "TypeLedRgbIo"
    61: "unknown",  # "TypeCloudNotif"
    62: "unknown",  # "TypeCloudInfo"
    63: "unknown",  # "TypeEthernetInfo"
    64: "unknown",  # "TypeMemoryInfo"
    65: "unknown",  # "TypeStorageInfo"
    66: "unknown",  # "TypeCpuInfo"
    67: "unknown",  # "TypeDiBusGwInfo"
}

MODULE_TYPE_DICTIONNARY: dict[str, dict[str, str | tuple]] = {
    "QG1": {
        "model": "DGQG01",
        "name": "Master",
        "mod_type_num": "00",
        "io_types_list": (
            "TypeIoNotHandled",
            "TypeVar",
            "TypeVarSys",
        ),
        "description": "First generation Master",
    },
    "QG2": {
        "model": "DGQG02",
        "name": "Master",
        "mod_type_num": "52",
        "io_types_list": (
            "TypeInputIo",
            "TypeTrvIo",
            "TypeTorIo",
            "TypeOut10VIo",
            "TypeAccessControlIo",
            "TypeLedIo",
            "TypeIoNotHandled",
            "TypeVar",
            "TypeVarSys",
            "TypeCloudNotif",
            "TypeCloudInfo",
            "TypeEthernetInfo",
            "TypeMemoryInfo",
            "TypeStorageInfo",
            "TypeCpuInfo",
            "TypeDiBusGwInfo",
        ),
        "description": "'All-in-one' Master",
    },
    "QG3": {
        "model": "DGQG03",
        "name": "Master",
        "mod_type_num": "53",
        "io_types_list": (
            "TypeInputIo",
            "TypeOut10VIo",
            "TypeTorIo",
            "TypeTrvIo",
            "TypeAccessControlIo",
            "TypeDali",
            "TypeIoNotHandled",
            "TypeVar",
            "TypeVarSys",
            "TypeCloudNotif",
            "TypeCloudInfo",
            "TypeEthernetInfo",
            "TypeMemoryInfo",
            "TypeStorageInfo",
            "TypeCpuInfo",
            "TypeDiBusGwInfo",
        ),
        "description": "'All-in-one' Master with DALI® interface",
    },
    "QG4": {
        "model": "DGQG04",
        "name": "Master",
        "mod_type_num": "54",
        "io_types_list": (
            "TypeIoNotHandled",
            "TypeVar",
            "TypeVarSys",
            "TypeCloudNotif",
            "TypeCloudInfo",
            "TypeEthernetInfo",
            "TypeMemoryInfo",
            "TypeStorageInfo",
            "TypeCpuInfo",
            "TypeDiBusGwInfo",
        ),
        "description": "Master",
    },
    "QG5": {
        "model": "DGQG05",
        "name": "Master",
        "mod_type_num": "67",
        "io_types_list": (
            "TypeTorIo",
            "TypeInputIo",
            "TypeTrvIo",
            "TypeLbIo",
            "TypeIoNotHandled",
            "TypeVar",
            "TypeVarSys",
            "TypeCloudNotif",
            "TypeCloudInfo",
            "TypeEthernetInfo",
            "TypeMemoryInfo",
            "TypeStorageInfo",
            "TypeCpuInfo",
            "TypeDiBusGwInfo",
        ),
        "description": "'All-in-one' Master with LightBus®",
    },
    "IS4": {
        "model": "DISM04",
        "mod_type_num": "0F",
        "io_types_list": ("TypeInputIo",),
        "io_offsets": (1, 2, 3, 4),
        "io_types": tuple([2] * 4),
        "nbr_of_bool_io": 4,
        "description": "Module with 4 inputs for dry contact",
    },
    "IS8": {
        "model": "DISM08",
        "mod_type_num": "01",
        "io_types_list": ("TypeInputIo",),
        "io_offsets": (1, 2, 3, 4, 5, 6, 7, 8),
        "io_types": tuple([2] * 8),
        "nbr_of_bool_io": 8,
        "description": "Module with 8 inputs for dry contact",
    },
    "I20": {
        "model": "DISM20",
        "mod_type_num": "46",
        "io_types_list": ("TypeInputIo",),
        "io_offsets": tuple(list(range(1, 21))),
        "io_types": tuple([2] * 20),
        "nbr_of_bool_io": 20,
        "description": "Module with 20 inputs for dry contact",
    },
    "BU1": {
        "model": "DPB(U/T)01",
        "mod_type_num": "02",
        "io_types_list": ("TypeInputIo", "TypeLedIo"),
        "io_offsets": (1, 1),
        "io_types": (2, 10),
        "nbr_of_bool_io": 1,
        "description": "1 Push Button",
    },
    "BU2": {
        "model": "DPB(U/T)02",
        "mod_type_num": "03",
        "io_types_list": ("TypeInputIo", "TypeLedIo"),
        "io_offsets": tuple([1, 2] * 2),  # (1, 2, 1, 2),
        "io_types": (2, 2, 10, 10),
        "nbr_of_bool_io": 2,
        "description": "2 Push Buttons",
    },
    "BU4": {
        "model": "DPB(U/T)04",
        "mod_type_num": "04",
        "io_types_list": ("TypeInputIo", "TypeLedIo"),
        "io_offsets": tuple([1, 2, 3, 4] * 2),
        "io_types": tuple([2] * 4 + [10] * 4),
        "nbr_of_bool_io": 4,
        "description": "4 Push Buttons",
    },
    "BU6": {
        "model": "DPB(U/T)06",
        "mod_type_num": "05",
        "io_types_list": ("TypeInputIo", "TypeLedIo"),
        "io_offsets": tuple([1, 2, 3, 4, 5, 6] * 2),
        "io_types": tuple([2] * 6 + [10] * 6),
        "nbr_of_bool_io": 6,
        "description": "6 Push Buttons",
    },
    "BRT": {
        "model": "DPBRT0x",
        "mod_type_num": "64",
        "io_types_list": ("TypeInputIo", "TypeSensorIo", "TypeLedRgbIo"),
        "description": "Rainbow - button with 2 to 6 RGB keys",
    },
    "BIR": {
        "model": "DBIR01",
        "mod_type_num": "06",
        "io_types_list": ("TypeTorIo",),
        "io_offsets": tuple(list(range(1, 9))),
        "io_types": tuple([1] * 8),
        "nbr_of_bool_io": 8,
        "description": "Relay Card - 8 bipolar outputs",
    },
    "V24": {
        "model": "DTRVBT01",
        "mod_type_num": "1E",
        "io_types_list": ("TypeTrvBtIo",),
        "io_offsets": (1,),
        "io_types": (7,),
        "description": "Low voltage motor module",  # 1 DC shutter command
    },
    "TPV": {
        "model": "DTRP02",
        "mod_type_num": "22",
        "io_types_list": ("TypeTrvIo",),
        "io_offsets": (1, 2),
        "io_types": (6, 6),
        "description": "Bi-directional switch module - 2 shutters",
    },
    "TRV": {
        "model": "DTRV01",
        "mod_type_num": "07",
        "io_types_list": ("TypeTrvIo",),
        "io_offsets": (1, 2, 3, 4),
        "io_types": (6, 6, 6, 6),
        "description": "Shutter module - 4 outputs",
    },
    "TRP": {
        "model": "DTRP01",
        "mod_type_num": "08",
        "io_types_list": ("TypeTorIo",),
        "io_offsets": (1, 2, 3, 4),
        "io_types": (1, 1, 1, 1),
        "nbr_of_bool_io": 4,
        "description": "Trip switch module - 4 outputs",  # 4 teleruptors
    },
    "DIM": {
        "model": "DDIM01",
        "mod_type_num": "09",
        "io_types_list": ("TypeDimmerIo",),
        "io_offsets": tuple(list(range(1, 9))),
        "io_types": tuple([3] * 8),
        "description": "Dimmer control module - 8 outputs",
    },
    "TE1": {
        "model": "DTEM01",
        "mod_type_num": "0A",
        "io_types_list": ("TypeSensorIo",),
        "io_offsets": (1,),
        "io_types": (8,),
        "description": "Temperature sensor",
    },
    "TE2": {
        "model": "DTEM02",
        "mod_type_num": "0B",
        "io_types_list": ("TypeSensorIo",),
        "io_offsets": (1,),
        "io_types": (8,),
        "description": "Temperature sensor with LCD",
    },
    "DIR": {
        "model": "DDIR0x",
        "mod_type_num": "0D",
        "io_types_list": ("TypeIrIo",),
        "io_offsets": (1,),
        "io_types": (9,),
        "description": "IR detector",
    },
    # "???": {
    #     "model": "DIREMIT01",
    #     "mod_type_num": "25",
    #     "io_types_list": ("TypeIrEmitIo"),
    #     "io_offsets": (1, 2, 3),
    #     "io_types": tuple(19, 19, 19),
    #     "description": "IR Transmitter – 3 channels",
    # },
    "LED": {
        "model": "DLED01",
        "mod_type_num": "0E",
        "io_types_list": ("TypeLedIo",),
        "io_offsets": (1, 2, 3, 4),
        "io_types": (10, 10, 10, 10),
        "nbr_of_bool_io": 4,
        "description": "4 leds driver",
    },
    "DMV": {
        "model": "DMV01",
        "mod_type_num": "17",
        "io_types_list": ("TypeFanIo", "TypeTorIo"),
        "io_offsets": (1, 2, 3, 1, 2),
        "io_types": (13, 13, 13, 1, 1),
        "description": "Mechanical ventilation",
    },
    "DET": {
        "model": "DMOV0x",  # DMOV01 02 05
        "mod_type_num": "18",
        "io_types_list": ("TypeMovIo",),
        "io_offsets": (1,),
        "io_types": (34,),
        "nbr_of_bool_io": 1,
        "description": "Motion detector",
    },
    "MV6": {
        "model": "DMOV06",
        "mod_type_num": "58",
        "io_types_list": ("TypeMovIo", "TypeLuxIo"),
        "description": "Motion and light detector",
    },
    "MV7": {
        "model": "DMOV07",
        "mod_type_num": "65",
        "io_types_list": ("TypeMovIo", "TypeLuxIo"),
        "description": "Motion and light detector",
    },
    "I10": {
        "model": "DIN10V02",
        "mod_type_num": "1F",
        "io_types_list": ("TypeIn10VIo", "TypeSensorIo"),  # Either one
        "io_offsets": (1, 1),
        "io_types": (21, 8),
        "description": "Input Module 0-10 Vdc",  # Analog 0-10V input
    },
    "AMP": {
        "model": "DAMPLI01",
        "mod_type_num": "23",
        "io_types_list": ("TypeSoundIo",),
        "io_offsets": (1, 2, 3, 4),
        "io_types": tuple([18] * 4),
        "description": "Sound Module",
    },
    "D10": {
        "model": "DOUT10V02",
        "mod_type_num": "24",
        "io_types_list": ("TypeOut10VIo",),
        "io_offsets": (1,),
        "io_types": (23,),
        "description": "0/1-10V dimmer module",
    },
    "PBL": {
        "model": "DPBTLCD0x",
        "mod_type_num": "26",
        "io_types_list": (
            "TypeInputIo",
            "TypeSensorIo",  # T° for odd serial number only
            "TypePbLcdIo",  # Which image is displayed (equivalent to ON/OFF)
        ),
        "io_offsets": (1, 2, 3, 4, 5, 6, 1, 1, 2, 3, 4, 5, 6),
        "io_types": (2, 2, 2, 2, 2, 2, 8, 20, 20, 20, 20, 20, 20),
        "nbr_of_bool_io": 6,
        "description": "LCD push buttons",
    },
    "FAN": {
        "model": "DFAN01",
        "mod_type_num": "27",
        "io_types_list": ("TypeDfanComboIo",),
        "io_offsets": (1,),
        "io_types": (12,),
        "description": "Fan controler",
    },
    "DMR": {
        "model": "DMR01",
        "mod_type_num": "28",
        "io_types_list": ("TypeTorIo",),
        "io_offsets": (1, 2, 3, 4, 5),
        "io_types": (1, 1, 1, 1, 1),
        "nbr_of_bool_io": 5,
        "description": "Relay card 5 single-pole outputs",
    },
    "PRL": {
        "model": "DPBRLCD02",
        "mod_type_num": "29",
        "io_types_list": ("TypeInputIo", "TypeSensorIo", "TypePbLcdIo"),
        "io_offsets": (1, 2, 3, 4, 5, 6, 1, 1, 2, 3, 4, 5, 6),
        "io_types": (2, 2, 2, 2, 2, 2, 8, 20, 20, 20, 20, 20, 20),
        "nbr_of_bool_io": 6,  # 1 to 6 depend of configuration
        "description": "Rainbow - LCD touchscreen - With temperature sensor",
    },
    "BR2": {
        "model": "DPBR02",
        "mod_type_num": "2A",
        "io_types_list": ("TypeInputIo", "TypeLedRgbIo"),
        "io_offsets": (1, 2, 1, 2),
        "io_types": (2, 2, 60, 60),
        "nbr_of_bool_io": 2,
        "description": "Rainbow - Glass button with 2 RGB keys",
    },
    "BR4": {
        "model": "DPBR04",
        "mod_type_num": "3C",
        "io_types_list": ("TypeInputIo", "TypeLedRgbIo"),
        "io_offsets": (1, 2, 3, 4, 1, 2, 3, 4),
        "io_types": (2, 2, 2, 2, 60, 60, 60, 60),
        "nbr_of_bool_io": 4,
        "description": "4 Push Button Rainbow (and RGB)",
    },
    "ET2": {
        "model": "DETH02",
        "mod_type_num": "2B",
        "io_types_list": ("TypeStringInputIo",),
        "description": "Ethernet Light Protocol module",
    },
    # "LCD": {
    #     "model": "DLCD01",
    #     "mod_type_num": "0C",
    #     "io_types_list": ("TypeInputIo",),
    #     "io_offsets": (1, 2),
    #     "io_types": tuple(2, 2),
    #     "description": "4*20 char LCD with 2 inputs",
    # },
    # "LC3": {
    #     "model": "DLCD03",
    #     "mod_type_num": "21",
    #     "io_types_list": ("TypeTorIo", "TypeInputIo", "TypeSensorIo"),
    #     "io_offsets": (1, 2, 1, 2, 1),
    #     "io_types": tuple(1, 1, 2, 2, 8),
    #     "description": "Multifunction LCD",
    # },
    # "TSB": {
    #     "model": "DTSC01/03",
    #     "mod_type_num": "11",
    #     "io_types_list": ("TypeInputIo", "TypeSensorIo"),
    #     "io_offsets": (1, 2, 1),
    #     "io_types": tuple(2, 2, 8),
    #     "description": "Multifunction LCD",
    # },
    "LT2": {
        "model": "DTSC02",
        "mod_type_num": "32",
        "io_types_list": (
            "TypeInputIo",
            "TypeSensorIo",
            "TypeIrIo",
            "TypeLedIo",
        ),
        "io_offsets": (1, 2, 3, 4, 1, 1, 1, 1, 1, 1, 1, 2, 3, 4, 1, 1, 1, 1, 1, 1, 1),
        "io_types": tuple(
            [2] * 4 + [8, 9, 8] + [0] * 3 + [10] * 4 + [18, 43] + [0, 1, 0, 31, 1]
        ),
        "nbr_of_bool_io": 4,
        "description": "TFT Touchscreen",
    },
    "LT4": {
        "model": "DTSC04",
        "mod_type_num": "37",
        "io_types_list": (
            "TypeInputIo",
            "TypeSensorIo",
            "TypeIrIo",
            "TypeLedIo",
        ),
        "io_offsets": (1, 2, 3, 4, 1, 1, 1, 1, 1, 1, 1, 2, 3, 4, 1, 1, 1, 1, 1, 1, 1),
        "io_types": tuple(
            [2] * 4 + [8, 9, 8] + [0] * 3 + [10] * 4 + [18, 43] + [0, 1, 0, 31, 1]
        ),
        "nbr_of_bool_io": 4,
        "description": "TFT touchscreen with video",
    },
    "LT5": {
        "model": "DTSC05",
        "mod_type_num": "55",
        "io_types_list": (
            "TypeInputIo",
            "TypeLedIo",
            "TypeSensorIo",
            "TypeVideoIo",
            "TypeHumidityIo",
            "TypeGestureIo",
        ),
        "description": "Rainbow - TFT color touchscreen",
    },
    "DMX": {
        "model": "DDMX01",
        "mod_type_num": "34",
        "io_types_list": ("TypeDmxIo",),
        "io_offsets": (1,),
        "io_types": (25,),
        "description": "DMX Module",
    },
    "DX2": {
        "model": "DDMX02",
        "mod_type_num": "4A",
        "io_types_list": ("TypeDmxIo",),
        "description": "DMX Module with RGBW",
    },
    "VI1": {
        "model": "DVIP01",
        "mod_type_num": "3A",
        "io_types_list": ("TypeVipDisplay",),
        "description": "",
    },
    "VI2": {
        "model": "DVIP02",
        "mod_type_num": "3E",
        "io_types_list": ("TypeInputIo", "TypeCamIo"),
        "description": "",
    },
    "DAL": {
        "model": "DINTDALI01",
        "mod_type_num": "3F",
        "io_types_list": ("TypeDali",),
        "io_offsets": tuple(list(range(1, 64))),
        "io_types": tuple([29] * 64),
        "description": "DALI interface",
    },
    "B81": {
        "model": "DPBL01",
        "mod_type_num": "41",
        "io_types_list": ("TypeInputIo", "TypeLed8cIo"),
        "io_offsets": (1, 1),
        "io_types": (2, 15),
        "nbr_of_bool_io": 2,
        "description": "1 Push Button Lythos (and 8 colors)",
    },
    "B82": {
        "model": "DPBL02",
        "mod_type_num": "42",
        "io_types_list": ("TypeInputIo", "TypeLed8cIo"),
        "io_offsets": tuple([1, 2] * 2),
        "io_types": tuple([2] * 2 + [15] * 2),
        "nbr_of_bool_io": 2,
        "description": "2 Push Buttons Lythos (and 8 colors)",
    },
    "B84": {
        "model": "DPBL04",
        "mod_type_num": "43",
        "io_types_list": ("TypeInputIo", "TypeLed8cIo"),
        "io_offsets": tuple([1, 2, 3, 4] * 2),
        "io_types": tuple([2] * 4 + [15] * 4),
        "nbr_of_bool_io": 4,
        "description": "4 Push Buttons Lythos (and 8 colors)",
    },
    "B86": {
        "model": "DPBL06",
        "mod_type_num": "44",
        "io_types_list": ("TypeInputIo", "TypeLed8cIo"),
        "io_offsets": tuple([1, 2, 3, 4, 5, 6] * 2),
        "io_types": tuple([2] * 6 + [15] * 6),
        "nbr_of_bool_io": 6,
        "description": "6 Push Buttons Lythos (and 8 colors)",
    },
    "BR6": {
        "model": "DPBR06",
        "mod_type_num": "45",
        "io_types_list": ("TypeInputIo", "TypeLedRgbIo"),
        "io_offsets": tuple([1, 2, 3, 4, 5, 6] * 2),
        "io_types": tuple([2] * 6 + [60] * 6),
        "nbr_of_bool_io": 6,
        "description": "Rainbow - Glass button with 6 RGB keys",
    },
    "MBD": {
        "model": "MBDEV01",
        "mod_type_num": "47",
        "io_types_list": (),
        "description": "ModBus Virtual Device",
    },
    "WI1": {
        "model": "DWIND01",
        "mod_type_num": "49",
        "io_types_list": ("TypeWindIo",),
        "description": "Wind sensor module",
    },
    "CL1": {
        "model": "DPBC01",
        "mod_type_num": "4C",
        "io_types_list": ("TypeInputIo", "TypeLed8cIo", "TypeSensorIo"),
        "io_offsets": (1, 1, 1),
        "io_types": (2, 15, 8),
        "nbr_of_bool_io": 1,
        "description": "1 Push Button Classic (8 colors and temperature sensor)",
    },
    "CL2": {
        "model": "DPBC02",
        "mod_type_num": "4D",
        "io_types_list": ("TypeInputIo", "TypeLed8cIo", "TypeSensorIo"),
        "io_offsets": (1, 2, 1, 2, 1),
        "io_types": (2, 2, 15, 15, 8),
        "nbr_of_bool_io": 2,
        "description": "2 Push Buttons Classic (8 colors and temperature sensor)",
    },
    "CL4": {
        "model": "DPBC04",
        "mod_type_num": "4E",
        "io_types_list": ("TypeInputIo", "TypeLed8cIo", "TypeSensorIo"),
        "io_offsets": (1, 2, 3, 4, 1, 2, 3, 4, 1),
        "io_types": (2, 2, 2, 2, 15, 15, 15, 15, 8),
        "nbr_of_bool_io": 4,
        "description": "4 Push Buttons Classic (8 colors and temperature sensor)",
    },
    "CL6": {
        "model": "DPBC06",
        "mod_type_num": "4F",
        "io_types_list": ("TypeInputIo", "TypeLed8cIo", "TypeSensorIo"),
        "io_offsets": (1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6, 1),
        "io_types": (2, 2, 2, 2, 2, 2, 15, 15, 15, 15, 15, 15, 8),
        "nbr_of_bool_io": 6,
        "description": "6 Push Buttons Classic (8 colors and temperature sensor)",
    },
    # "DLB": {
    #     "model": "DLB01",
    #     "mod_type_num": "51",
    #     "io_types_list": ("TypeLbIo"),  # Normally not directly addressable
    #     "description": "Low-voltage LED dimmer",
    # },
    "EV1": {
        "model": "DENV01",
        "mod_type_num": "56",
        "io_types_list": (
            "TypeSensorIo",
            "TypeLuxIo",
            "TypeHumidityIo",
            "TypePressureIo",
        ),
        "description": "Environment sensor module",
    },
    "EV2": {
        "model": "DENV02",
        "mod_type_num": "57",
        "io_types_list": ("TypeSensorIo", "TypeHumidityIo", "TypeCo2Io"),
        "description": "Environment sensor module with CO2 sensor",
    },
    "LV1": {
        "model": "DDIMLV01",
        "mod_type_num": "5A",
        "io_types_list": ("TypeLbIo"),
        "description": "Lighting interface for domintell current dimmer",
    },
    "RW1": {
        "model": "DRGBW01",
        "mod_type_num": "5C",
        "io_types_list": (
            "TypeRgbwIo",
            "TypeDimmerIo",
        ),
        "description": "RGBW LED strips controller",
    },
    "NT1": {
        "model": "DNET01",
        "mod_type_num": "48",
        "io_types_list": (
            "TypeNetworkTextIo",
            "TypeIoNotHandled",
            "TypeVar",
            "TypeVarSys",
            "TypeDiBusGwInfo",
        ),
        "description": "Universal Ethernet Interface",
    },
    "NT2": {
        "model": "DNET02",
        "mod_type_num": "5D",
        "io_types_list": (
            "TypeNetworkTextIo",
            "TypeIoNotHandled",
            "TypeVar",
            "TypeVarSys",
        ),
        "description": "Universal Ethernet Interface",
    },
    "PS4": {
        "model": "DALI04",
        "mod_type_num": "5E",
        "io_types_list": ("TypePowerSupplyIo",),
        "description": "Smart stabilized power supply 20 W",
    },
    "PS5": {
        "model": "DALI05",
        "mod_type_num": "5F",
        "io_types_list": ("TypePowerSupplyIo",),
        "description": "Smart stabilized power supply 60 W",
    },
    "RT1": {
        "model": "DPBRTHERM01",
        "mod_type_num": "66",
        "io_types_list": ("TypeSensorIo",),
        "description": "Rainbow - Thermostat",
    },
    "EL1": {
        "model": "DELEC01",
        "name": "Wifi P1 meter",
        "mod_type_num": "68",
        "io_types_list": ("TypeElecIo",),
        "description": "Wi-Fi P1 counter",
    },
    "MON": {
        "model": "DMONOELEC01",
        "mod_type_num": "2E",
        "io_types_list": ("TypeElecIo",),
        "description": "Measuring module - Single-phase consumption",
    },
    "TRI": {
        "model": "DTRIELEC01",
        "mod_type_num": "2F",
        "io_types_list": ("TypeElecIo",),
        "description": "Measuring module - Three-phase consumption",
    },
    "MR2": {
        "model": "DMR02",
        "mod_type_num": "6A",
        "io_types_list": ("TypeTorIo",),
        "description": "Relay card with 8 monopolar",
    },
    "DST": {
        "model": "DOORSTATION",
        "mod_type_num": "F5",
        "io_types_list": (
            "TypeInputIo",  # Virtual unlock door push-button
            "TypeMovIo",  # Motion Detector
            "TypeTorBasicTempoIo",  # Relay: electric strike
            "TypeInputTriggerIo",  # Calling push-button
        ),
        "description": "Doorstation",
    },
    # "MB2": {
    #     "model": "DINTMB02",
    #     "mod_type_num": "F1", #TODO it has no module_type
    #     "io_types_list": (
    #         "TypeInputIo",
    #         "TypeSensorIo",
    #         "TypeFanIo",
    #         "TypeElecIo",
    #         "TypeVanesIo",
    #         "TypeDeviceStatus",
    #         "TypePercentInIo",
    #         "TypeAnalogInIo",
    #     ),
    #     "description": "ModBus interface RTU",
    # },
    "MBG": {
        "model": "ModBus generic device",
        "mod_type_num": "F1",
        "io_types_list": (
            "TypeInputIo",
            "TypeSensorIo",
            "TypeFanIo",
            "TypeElecIo",
            "TypeVanesIo",
            "TypeDeviceStatus",
            "TypePercentInIo",
            "TypeAnalogInIo",
        ),
        "description": "ModBus generic device",
    },
    "MBA": {
        "model": "Air conditioner device",
        "mod_type_num": "F3",
        "io_types_list": (
            "TypeSensorIo",
            "TypeFanIo",
            "TypeVanesIo",
            "TypeDeviceStatus",
        ),
        "description": "Air conditioner device",
    },
    "CLK": {
        "model": "CLOCK",
        "mod_type_num": "F6",
        "io_types_list": ("TypeClock",),
        "io_offsets": (1,),
        "io_types": (45,),
        "description": "Clock",
    },
    "SFE": {
        "model": "SCENE",
        "mod_type_num": "FB",
        "io_types_list": ("TypeIoNotHandled",),
        "io_offsets": (1,),
        "io_types": (0,),
        "description": "Scene",
    },
    "MEM": {
        "model": "GROUP",
        "mod_type_num": "FC",
        "io_types_list": (
            "TypeTorIo",
            "TypeDimmerIo",
            "TypeTrvIo",
            "TypeDmxIo",
            "TypeDfanComboIo",
            "TypeFanIo",
            "TypeDali",
            "TypeLbIo",
            "TypeRgbwIo",
            "TypeSoundIo",
        ),
        "description": "Memo",
    },
    "SYS": {
        "model": "SYSVAR",
        "mod_type_num": "FD",
        "io_types_list": ("TypeVarSys",),
        "io_offsets": (1,),
        "io_types": (17,),
        "description": "System variable",
    },
    "VAR": {
        "model": "VAR",
        "mod_type_num": "FE",
        "io_types_list": ("TypeVar",),
        "io_offsets": (1,),
        "io_types": (16,),
        "description": "Variable",
    },
}


LEGACY_DATA_TYPE_LIST = ("I", "O", "D", "X", "T", "U", "C", "S", "P", "K")
IOTYPE_OF_LEGACY_DATA_TYPE: dict[str, str] = {
    "I": "TypeInputIo",
    "O": "TypeTorIo",  # or TypeLedIo, TypeLed8cIo, TypeTrvIo, TypeDfanComboIo
    "D": "TypeDimmerIo",  # or TypeOut10VIo, TypeIn10V
    "X": "TypeDmxIo",
    "T": "TypeSensorIo",
    "U": "TypeSensorIo",
    "C": "TypeIrIo",
    "S": "TypeSoundIo",
    "K": "TypeClock",
}

IOTYPE_OF_GROUP_CATEGORY: dict[str, int] = {
    "MIX": 1,  # TypeTorIo
    "DIMMERS": 3,  # TypeDimmerIo
    "SHUTTERS": 6,  # TypeTrvIo
    "DMX": 25,  # TypeDmxIo
    "FAN": 12,  # TypeDfanComboIo
    "DMV": 13,  # TypeFanIo
    "DALI": 29,  # TypeDali
    "DLB": 42,  # TypeLbIo
    "RGBW": 46,  # TypeRgbwIo
    "SOUND": 18,  # TypeSoundIo
}


NOT_A_MODULE_TYPE_LIST = ("SFE", "SYS", "VAR", "MEM")

MODULE_TYPE_OF_MODULES_WITH_NO_IO = ("NT1", "NT2", "QG1", "QG4")

MASTER_MODULE_TYPE_LIST = (
    "QG1",
    "QG2",
    "QG3",
    "QG4",
    "QG5",
)

DNET_MODULE_TYPE_LIST = (
    "NT1",
    "NT2",
)

GATEWAY_MODULE_TYPE_LIST = MASTER_MODULE_TYPE_LIST + DNET_MODULE_TYPE_LIST

SHUTTERS_MODULE_TYPE_LIST = ("V24", "TRV", "TPV")
LED_INDICATOR_IO_TYPE_LIST = (10, 15, 20, 60)
SENSORS_IO_TYPE_LIST = (8, 21, 24, 34, 36, 37, 38, 39, 41, 51, 56, 57)
SENSORS_TARGET_TYPE_LIST = (
    "sensor",
    "motion",
    "contact",
    "temperature",
    "analog",
    "illuminance",
    "humidity",
    "pressure",
    "carbon_dioxide",
    "wind",
    "power_supply",
    "electricity",
    "analog",
)

BUTTONS_MODULE_TYPE_LIST = (
    "BU1",
    "BU2",
    "BU4",
    "BU6",
    "BRT",
    "PBL",
    "PRL",
    "BR2",
    "BR4",
    "B81",
    "B82",
    "B84",
    "B86",
    "BR6",
    "CL1",
    "CL2",
    "CL4",
    "CL6",
    "PRL",
)

LEGACY_MODULE_DMX_LIST = ("DMX",)
LEGACY_MODULE_WITH_TEMP_SENSOR_LIST = (
    "TE1",
    "TE2",
    "PBL",
    "PRL",
    "CL1",
    "CL2",
    "CL4",
    "CL6",
    "LT2",
    "LT4",
    "LC3",
    "TSB",
)

cmd_type_new_gen: dict[str, int] = {
    "Start of detection": 1,
    "End of detection": 2,
    "Start of short push": 1,
    "End of short push": 2,
    "Start of long push": 3,
    "End of long push": 4,
    "Gesture right": 2,
    "Gesture left": 3,
    "Gesture up": 4,
    "Gesture down": 5,
    "Gesture push": 6,
    "Toggle": 1,
    "On": 2,
    "Off": 3,
    "Set Value": 5,
    "Move Up": 10,
    "Move Down": 11,
    "Increase": 16,
    "Decrease": 17,
    "Set Color": 71,
    "Color Cycle": 77,
    "Set Heating Setpoint": 1,
    "Set Cooling Setpoint": 2,
    "Set Mode Temperature": 55,
    "Set Mode Regulation": 82,
    "Get Status": 103,
    "Simulate Push": 104,  # (from PROG M 43.7)
}

cmd_type_legacy: dict[str, str] = {
    "Start of detection": "%P1",
    "End of detection": "%P2",
    "Start of short push": "%P1",
    "End of short push": "%P2",
    "Start of long push": "%P3",
    "End of long push": "%P4",
    "Toggle": "",
    "On": "%I",
    "Off": "%O",
    "Set Value": "%D",
    "Move Up": "%H",
    "Move Down": "%L",
    "Increase": "%I%D",
    "Decrease": "%O%D",
    "Set Color": f"%X",
    "Color Cycle": "%C",
    "Set Heating Setpoint": "%T",
    "Set Cooling Setpoint": "%U",
    "Set Mode Temperature": "%M",
    "Set Mode Regulation": "%R",
    "Get Status": "%S",
}


def get_cmd_legacy(cmd: str) -> str:
    """Return the legacy command"""
    return cmd_type_legacy.get(cmd, None)


def get_cmd_new_gen(cmd: str) -> str:
    """Return the new gen command"""
    return cmd_type_new_gen.get(cmd, None)


def is_module_newgen(module_type: str) -> bool:
    """Return True if module is new gen"""
    return module_type not in LEGACY_MODULE_TYPE_LIST


def is_module_legacy(module_type: str) -> bool:
    """Return True if module is legacy"""
    return module_type in LEGACY_MODULE_TYPE_LIST


def is_module_master(module_type: str) -> bool:
    """Return True if module is master"""
    return module_type in MASTER_MODULE_TYPE_LIST


def is_module_dnet(module_type: str) -> bool:
    """Return True if module is DNET0x"""
    return module_type in DNET_MODULE_TYPE_LIST


def get_module_type_num_by_model(model_name: str):
    """Return module type number of model"""
    for module_type, module_data in MODULE_TYPE_DICTIONNARY.items():
        if module_data["model"] == model_name:
            return module_data["mod_type_num"]
    return None


def get_module_type_by_model(model_name: str):
    """Return module type of model"""
    for module_type, module_data in MODULE_TYPE_DICTIONNARY.items():
        if module_data["model"] == model_name:
            return module_type
    return None
