import re
import copy
import traceback

from .const import (
    IO_TYPES_STRING,
    IO_TYPES_INT,
    MODULE_TYPE_DICTIONNARY,
    IO_DEFAULT_TARGET_TYPES,
    LEGACY_MODULE_TYPE_LIST,
    LEGACY_MODULE_DMX_LIST,
    LEGACY_MODULE_WITH_TEMP_SENSOR_LIST,
    IOTYPE_OF_LEGACY_DATA_TYPE,
    IOTYPE_OF_GROUP_CATEGORY,
    SUPPORTED_MODULE_TYPE_LIST,
    SUPPORTED_IO_TYPE_LIST,
    SHUTTERS_MODULE_TYPE_LIST,
    BUTTONS_MODULE_TYPE_LIST,
    cmd_type_new_gen,
    cmd_type_legacy,
)


def is_new_gen_status(message: str) -> bool:
    return "/" in message


def is_legacy_status(message: str) -> bool:
    return "/" not in message


def is_new_gen_module(module_type: str) -> bool:
    return not is_legacy_module(module_type)


def is_legacy_module(module_type: str) -> bool:
    return module_type in LEGACY_MODULE_TYPE_LIST


def is_hour_message(message: str) -> bool:
    date_regex = r"^([0-9]{2}):([0-9]{2}) ([0-9]{2})\/([0-9]{2})\/([0-9]{2,4}).*$"
    match = re.search(date_regex, message)
    return match is not None


def is_clock_status(message: str) -> bool:
    return message.startswith("CLK")


def construct_endpoint_id(data: str):
    if "/" in data:
        # NewGen format
        msg_tab = data.split("/")
        module_type = msg_tab[0]

        try:
            end_of_sn = int(msg_tab[1])
            io_type = int(msg_tab[2])
            io_offset = int(msg_tab[3])
        except ValueError as ex:
            raise ValueError("Invalid data format") from ex

        # Formatting end_of_sn
        end_of_sn_hex = f"{end_of_sn:06X}"  # formatting with 0-padding to 6 digits
        endpoint_id = f"{module_type}{end_of_sn_hex}-{io_type}-{io_offset}"
    else:
        # Legacy format
        module_type = data[:3].strip()
        end_of_sn = data[3:9].replace(" ", "0")

        if module_type == "SFE":
            end_of_sn = "000000"
            io_type = 0  # TypeIoNotHandled
            io_offset = int(data[3:9], 16)

        elif module_type == "VAR":
            end_of_sn = "000000"
            io_type = 16  # TypeVar
            io_offset = int(data[3:9], 16)

        elif module_type == "SYS":
            end_of_sn = "000000"
            io_type = 17  # TypeVarSys
            io_offset = int(data[3:9], 16)

        else:
            if module_type == "DAL":
                io_num_str = data[10] + data[11]
            else:
                io_num_str = data[10]

            # Ignore lines for pairs io num
            if (module_type in ("V24", "TRV", "TPV")) and (
                (int(io_num_str, 16) % 2) == 0
            ):
                return None

            # io_num must convert to shutter numbers
            if module_type in ("TPV", "TRV") and io_num_str != "1":
                io_num = int(io_num_str, 16)  # 3,5,7  -> 2,3,4
                io_num_str = str((io_num + 1) // 2)

            # Determine the io offset and io type
            try:
                # Determine the io offset
                io_num = int(io_num_str, 16)
                io_offset = MODULE_TYPE_DICTIONNARY.get(module_type)["io_offsets"][
                    io_num - 1
                ]
                # Determine the io type
                io_type: int = MODULE_TYPE_DICTIONNARY.get(module_type)["io_types"][
                    io_num - 1
                ]
            except ValueError as ex:
                raise ValueError("Invalid io_offset format") from ex

            # Case of LT2 and LT4: not all io supported
            if module_type in ("LT2", "LT4"):
                if io_num in (7, 8, 9, 10, 15):
                    return None

        # Endpoint Id construction
        endpoint_id: str = (
            module_type + end_of_sn + "-" + str(io_type) + "-" + str(io_offset)
        )

    return endpoint_id


class LpStatus:
    def __init__(self, message: str):
        self._raw_message = message.strip()
        self._id: str = ""
        self._serial_number: str = ""
        self._module_type: int = 0
        self._io_type: int = 0
        self._io_offset: int = 0
        self._raw_data: str = ""
        self._data: list = []
        self._status_requested: bool = False
        self._legacy: bool = True

        if message is not None and len(message) > 0:
            self._parse_status_message(message.strip())
        else:
            raise ValueError("message is empty")

    @property
    def message(self) -> str:
        return self._raw_message

    @property
    def id(self) -> str:
        return self._id

    @property
    def serial_number(self) -> str:
        return self._serial_number

    @property
    def module_type(self) -> str:
        return self._module_type

    @property
    def io_type(self) -> int:
        return self._io_type

    @property
    def io_offset(self) -> int:
        return self._io_offset

    @property
    def data(self) -> list:
        return self._data

    @property
    def is_legacy(self) -> bool:
        return self._legacy

    # @property
    # def get_dict(self) -> dict:
    #     exclude = {"_raw_message", "_raw_data"}
    #     return {
    #         key: value for key, value in self.__dict__.items() if key not in exclude
    #     }

    @property
    def get_dict(self) -> dict:
        exclude = {"_raw_message", "_raw_data"}
        return {
            key[1:]: value
            for key, value in self.__dict__.items()
            if key not in exclude and key.startswith("_")
        }

    def __str__(self):
        return 'LpStatus (Id: "{}", Serial Number: "{}", Module Type: "{}", Io Type: {} ({}), Io Offset: {}, Raw Data: "{}", Data: {}, Status Requested: {}, Legacy: {})'.format(
            self._id,
            self._serial_number,
            self._module_type,
            self._io_type,
            IO_TYPES_STRING.get(self._io_type, "TypeIoNotHandled"),
            self._io_offset,
            self._raw_data,
            self._data,
            self._status_requested,
            self._legacy,
        )

    def _parse_raw_data_legacy(self):
        data: list = []

        if self._io_type == 8:  # TypeSensorIo
            # Raw Data Format for Temperature frame status -> "T18.6 0.0 AUTO 0.0" or "U18.6 0.0 AUTO 0.0"
            try:
                if (self._raw_data[0] == "T") or (self._raw_data[0] == "U"):
                    elements = self._raw_data[1:].split()
                    data.append(self._raw_data[0])  # Data Type (T or U)
                    data.append(float(elements[0]))  # Current temperature
                    data.append(float(elements[1]))  # Active heating/cooling setpoint
                    data.append(elements[2])  # Current temperature mode
                    data.append(float(elements[3]))  # Profile Heating/cooling setpoint
            except ValueError as ex:
                raise ValueError("Invalid data for temperature sensor") from ex

        elif self._io_type == 18:  # self._module_type == "AMP"
            # Raw Data Format: "1-1D-TUNE-6A-0FA0" -> Output 1, 29%, Tuner, 106.4000MHz
            try:
                elements = self._raw_data.split("-")

                # ignore output number
                data.append(int(elements[1], 16))
                data.append(elements[2])
                int_part = int(elements[3], 16)
                dec_part = int(elements[4], 16)
                frec_str = str(int_part) + "." + str(dec_part)
                data.append(float(frec_str))
            except ValueError as ex:
                raise ValueError("Invalid data for Ampli") from ex
        elif self._io_type in (6, 7):  # TypeTrvIo or TypeTrvBtIo
            # "V24" (1 output), "TPV" (2 outputs), "TRV" (4 outputs)
            try:
                output_state = int(self._raw_data, 16)
                if self.module_type == "V24":
                    binary_string = bin(output_state)[2:].zfill(2)
                elif self.module_type == "TPV":
                    binary_string = bin(output_state)[2:].zfill(4)
                else:
                    # "TRV"
                    binary_string = bin(output_state)[2:].zfill(8)

                quatuors_bits = [
                    int(binary_string[i : i + 2], 2)
                    for i in range(0, len(binary_string), 2)
                ]
                data = quatuors_bits[::-1]  # Invert list

            except ValueError as ex:
                raise ValueError("Invalid raw data (not in hexadecimal format)") from ex
        elif self._io_type == 12:  # TypeDfanComboIo (FAN DFAN01)
            try:
                speed_mask = 0b111
                heating_mask = 0b11000
                mode_mask = 0b100000

                output_state = int(self._raw_data, 16)
                speed = output_state & speed_mask
                heating = (output_state & heating_mask) >> 3
                mode = (output_state & mode_mask) >> 5

                if speed == 4:
                    speed = 3

                if heating == 0:
                    heating = "OFF"
                elif heating == 1:
                    heating = "HEATING"
                else:
                    heating = "COOLING"

                if mode == 0:
                    mode = "AUTO"
                else:
                    mode = "MANUAL"

                data = [speed, heating, mode]
            except ValueError as ex:
                raise ValueError("Invalid raw data (not in hexadecimal format)") from ex
        elif self._io_type == 13:  # TypeFanIo (DMV DMV01)
            try:
                speed_mask = 0b111
                aux1_mask = 0b01000
                aux2_mask = 0b10000

                output_state = int(self._raw_data, 16)
                speed = output_state & speed_mask
                aux1 = (output_state & aux1_mask) >> 3
                aux2 = (output_state & aux2_mask) >> 4

                if speed == 4:
                    speed = 3

                data = [speed, aux1, aux2]
            except ValueError as ex:
                raise ValueError("Invalid raw data (not in hexadecimal format)") from ex
        elif self._io_type == 45:  # TypeClock
            # Raw Data Format: "17:16:34 7F 00/00/00 00:00:00"
            # TODO can be used the number as io_offset
            try:
                data = self._raw_data.split(" ")
            except ValueError as ex:
                raise ValueError("Invalid raw data (not in hexadecimal format)") from ex
        elif self._module_type in (
            "DIM",
            "D10",
            "I10",
            "DMX",
            "DAL",
        ) or ((self._io_type == 16) and (self._data_type == "D")):
            # Raw Data Format: <data> (n * 2 char hexa)
            # Split by 2-character chunks and convert to integers
            try:
                self._raw_data = self._raw_data.replace(" ", "0")
                data = [int(part, 16) for part in re.findall(r".{2}", self._raw_data)]
            except ValueError as ex:
                raise ValueError("Invalid raw data (not in hexadecimal format)") from ex
        else:
            # For TypeTorIo, TypeInputIo, TypeLedIo, TypeLed8cIo, TypeLedRgbIo, TypePbLcdIo, TypeRgbwIo, TypeMovIo
            # Eventually for TypeVar, TypeVarSys,
            # of legacy modules, generaly relays, buttons, leds and ism (LT4 and LT2)

            # Raw Data Format: <data> (n * 2 char hexa)
            # Parse single value as hexadecimal integer
            try:
                self._raw_data = self._raw_data.replace(" ", "0")
                output_state = int(self._raw_data, 16)
            except ValueError as ex:
                raise ValueError("Invalid raw data (not in hexadecimal format)") from ex

            nbr_bool = MODULE_TYPE_DICTIONNARY.get(self._module_type, {}).get(
                "nbr_of_bool_io", 8
            )
            # Convert to list of individual bits
            data = [0] * nbr_bool
            the_range = range(nbr_bool)

            for i in the_range:
                shift = i
                mask = 1 << shift
                data[i] = (output_state & mask) >> shift

        return data

    def _parse_raw_data_new_gen(self):
        # Raw Data Format: <data1>#<data2>#... or <data1>|<data2>|...

        # Split the data based on separators
        data = (
            self._raw_data.split("#")
            if "#" in self._raw_data
            else self._raw_data.split("|")
        )

        # Handle different IO types requiring data processing
        if self.io_type == 8:  # "TypeSensorIo":
            # Temperature unit = "°C" (CELCIUS)
            try:
                data[0] = float(data[0])  # Current temperature
                data[1] = float(data[1])  # Active heating setpoint
                data[2] = data[2]  # Current temperature mode
                data[3] = float(data[3])  # Profile Heating setpoint
                data[4] = float(data[4])  # Active Cooling setpoint
                data[5] = data[5]  # Current regulation mode
                data[6] = float(data[6])  # Profile cooling setpoint
            except ValueError as ex:
                raise ValueError("Invalid data for sensor io") from ex

        elif self.io_type == 24:  # "TypeElecIo"
            # Example data:
            # <feature_flags>|<frequency>|<power_factor_l1>|<power_factor_l2>|
            # <power_factor_l3>|<voltage_l1>|<voltage_l2>|<voltage_l3>|
            # <intensity_l1>|<intensity_l2>|<intensity_l3>|<instant_power_l1>|
            # <instant_power_l2>|<instant_power_l3>|<consumed_power>|
            # <produced_power>|<total_power>|<total_energy_l1>|<total_energy_l2>|
            # <total_energy_l3>|<forward_energy>|<reverse_energy>|<total_energy>|
            # <total_energy_for_t1>|<total_energy_for_t2>|<total_energy_for_t3>|
            # <total_energy_for_t4>|<tariff_indicator>

            try:
                data[0] = data[0].upper()  # feature_flags in hex format
                data[1] = float(data[1])  # frequency
                data[2] = float(data[2])  # power_factor_l1
                data[3] = float(data[3])  # power_factor_l2
                data[4] = float(data[4])  # power_factor_l3

                for i in range(5, 28):
                    data[i] = int(data[i])
            except ValueError as ex:
                raise ValueError("Invalid data for electricity io") from ex

        elif self.io_type in (25, 46, 60):
            # "TypeDmxIo"
            # Example data (DMX): "0|0|0" or "0|0|0#0|0|0"(multi io)
            # ["0|0|0", "0|0|0"] -> [[0, 0, 0], [0, 0, 0]] <- [[r,g,b], [r,g,b]]
            # ["0", "0", "0"] -> [[0, 0, 0]]] [r,g,b]

            # "TypeLedRgbIo"
            # Example data (LedRGB): "1|255|0|0" or "1|255|0|0#1|255|0|0"(multi io)
            # ["1|255|0|0", "1|255|0|0"] -> [[1, 255, 0, 0], [1, 255, 0, 0]] [on/off, r,g,b]
            # ["1", "255", "0", "0"] -> [[1, 255, 0, 0]] [on/off, r,g,b]

            # "TypeRgbwIo"
            # Example data (RGBW): "1|255|0|0" or "1|255|0|0#1|255|0|0"(multi io)
            # ["50"|255|0|0", "25|255|0|0"] -> [[50, 255, 0, 0], [25, 255, 0, 0]] [r,g,b,w]
            # ["65", "255", "0", "0"] -> [[65, 255, 0, 0]] [r,g,b,w]
            # Note: If color cyrcle is running an extra channel value is set
            # ["50", "255", "0", "0", "204"] -> [[50, 255, 0, 0, 204]] [r,g,b,w,c]
            try:
                if len(data) > 1:
                    if "|" in data[0]:
                        for index, channel in enumerate(data):
                            tmp = channel.split("|")
                            tmp_int = [int(x) for x in tmp]
                            data[index] = tmp_int
                    else:
                        tmp_int = [int(x) for x in data]
                        data = [tmp_int]

            except ValueError as ex:
                raise ValueError("Invalid data for color io") from ex

        elif self.io_type in (14, 31):  # "TypeCamIo", "TypeVideoIo"
            # Example data: "0x04"
            try:
                data[0] = data[0].upper()  # flags in hex format

            except ValueError as ex:
                raise ValueError("Invalid data for Cam/Video io") from ex

        elif self.io_type in (37, 38, 39, 57):
            # "TypeHumidityIo", "TypePressureIo", "TypeCo2Io", "TypeAnalogInIo"
            # Example data: "56.6"
            try:
                data[0] = float(data[0])
            except ValueError as ex:
                raise ValueError("Invalid data for sensor") from ex

        elif self.io_type == 40:  # "TypeAccessControlIo"
            # For this io type, status is empty
            data[0] = ""

        elif self.io_type == 41:  # "TypeWindIo"
            # Example of data: "10.0|NE" -> <wind speed>|<wind direction>
            try:
                data[0] = float(data[0])  # Wind speed in "km/h"
                data[1] = data[1]  # Wind direction (N, S, E, W, ...)
            except ValueError as ex:
                raise ValueError("Invalid data for wind sensor") from ex

        elif self.io_type == 43:  # "TypeGenericSoundIo"
            for i in range(0, 4):
                data[i] = int(data[i])
            data[4] = data[4]

        elif self.io_type == 51:  # "TypePowerSupplyIo"
            # Example data: "19|15.1|39"
            try:
                data[0] = int(data[0])  # Load in %
                data[1] = float(data[1])  # Voltage in Volt
                data[2] = float(data[2])  # Internal temperature in °C

            except ValueError as ex:
                raise ValueError("Invalid data for power supply sensor") from ex

        elif self.io_type == 55:  # "TypeDeviceStatus"
            # For this io type, status is empty
            # TODO not supported at the moment
            data[0] = ""

        elif self.io_type == 56:  # "TypePercentInIo"
            # Example data: "34"
            data[0] = int(data[0])  # in %

        elif self.io_type == 58:  # "TypeAccessControlCardItem"
            # For this io type, status is empty
            # TODO not supported at the moment
            data[0] = ""

        elif self.io_type == 62:  # "TypeCloudInfo"
            for i in range(0, 4):
                data[i] = int(data[i])
            data[4] = data[4]  # error description (UTF-8 string)

        elif self.io_type == 64:  # "TypeMemoryInfo"
            # TODO not supported at the moment
            data[0] = ""

        elif self.io_type == 65:  # "TypeStorageInfo"
            # TODO not supported at the moment
            data[0] = ""

        elif self.io_type == 66:  # "TypeCpuInfo"
            # TODO not supported at the moment
            data[0] = ""

        elif self.io_type == 67:  # "TypeDiBusGwInfo"
            # TODO not supported at the moment
            data[0] = ""

        # Handle other IO types
        else:
            data = list(map(int, data))

        return data

    def _parse_newgen_message(self, message: str):
        # Frame Format New Gen: <Module type>/<serial number without mod type>/<IO type>/<IO offset>/<data1>#<data2>#...
        msg_tab = message.split("/")
        self._module_type = msg_tab[0]
        self._raw_data = msg_tab[4]
        self._status_requested = msg_tab.pop() == "S"

        try:
            end_of_sn = int(msg_tab[1])
            self._io_type = int(msg_tab[2])
            self._io_offset = int(msg_tab[3])
        except ValueError as ex:
            raise ValueError("Invalid message format") from ex

        # Ignore unsupported io_type
        if self._io_type not in SUPPORTED_IO_TYPE_LIST:
            raise TypeError(f"Unsupported io type: {self._io_type}")

        # Formatting end_of_sn
        end_of_sn_hex = f"{end_of_sn:06X}"  # formatting with 0-padding to 6 digits

        module_type_num = MODULE_TYPE_DICTIONNARY.get(self._module_type)["mod_type_num"]
        self._serial_number = module_type_num + end_of_sn_hex

        self._id = (
            f"{self._module_type}{end_of_sn_hex}-{self._io_type}-{self._io_offset}"
        )

        self._data = self._parse_raw_data_new_gen()

    def _parse_legacy_message(self, message: str):
        # Frame Format Legacy: <Module type> + <serial number 6 char hexadecimal> + <optional io number> + <data type> + <Data>
        self._module_type = message[:3]
        end_of_sn = message[3:9].replace(" ", "0")

        # Note: we can haveTPR,TPL et STA which do not exist in the module type
        module_type_num = MODULE_TYPE_DICTIONNARY.get(self._module_type)["mod_type_num"]
        self._serial_number = module_type_num + end_of_sn

        # Case of DMX, DAL, AMP or ...
        # data_type possible letters I, O, D, X, T, U, C, S, P, K
        if self._module_type == "DMX":
            self._io_offset = int(message[10], 16)
            data_type = message[11]
            if message[11] == "-":  # Legacy format
                data_type = "X"
        elif self._module_type == "DAL":
            self._io_offset = int(message[10] + message[11], 16)
            data_type = message[12]
        elif self._module_type == "AMP":
            self._io_offset = int(message[10], 16)
            data_type = message[9]
        elif self._module_type in ("CLK", "SFE", "SYS", "VAR", "MEM"):
            self._serial_number = module_type_num + "000000"
            self._io_offset = int(end_of_sn, 16)
            data_type = message[9]
        else:
            self._io_offset = 1
            data_type = message[9]

        # TODO il faudrait une fonction qui prend module_type et data_type et retourne io_type

        io_type_str = IOTYPE_OF_LEGACY_DATA_TYPE.get(data_type)
        self._io_type = IO_TYPES_INT.get(io_type_str, 0)

        if data_type == "O":  # Outputs
            if self._module_type == "VAR":
                self._io_type = 16  # TypeVar
            elif self._module_type == "SYS":
                self._io_type = 17  # TypeVarSys
            elif self._module_type in (
                "BR2",
                "BR4",
                "BR6",
            ):
                self._io_type = 60  # TypeLedRgbIo
            elif self._module_type in (
                "LED",
                "BU1",
                "BU2",
                "BU4",
                "BU6",
                "LT2",
                "LT4",
                "LT5",
            ):
                self._io_type = 10  # TypeLedIo
            elif self._module_type in (
                "B81",
                "B82",
                "B84",
                "B86",
                "CL1",
                "CL2",
                "CL4",
                "CL8",
            ):
                self._io_type = 15  # TypeLed8cIo
            elif self._module_type in ("TRV", "TPV"):
                self._io_type = 6  # TypeTrvIo
            elif self._module_type in ("V24"):
                self._io_type = 7  # TypeTrvBtIo
            elif self._module_type == "FAN":
                self._io_type = 12  # TypeDfanComboIo
            elif self._module_type == "DMV":
                self._io_type = 13  # TypeFanIo
            else:
                self._io_type = 1  # TypeTorIo
        elif data_type == "I":  # Inputs
            if self._module_type == "DET":
                self._io_type = 34  # TypeMovIo
            else:
                self._io_type = 2  # TypeInputIo
        elif data_type == "D":  # Percent value
            if self._module_type == "VAR":
                self._io_type = 16  # TypeVar
            elif self._module_type == "D10":
                self._io_type = 23  # TypeOut10VIo
            elif self._module_type == "I10":
                self._io_type = 21  # TypeIn10VIo
            elif self._module_type == "DAL":
                self._io_type = 29  # TypeDali
            else:
                self._io_type = 3  # TypeDimmerIo
        elif data_type == "C":  # IR code
            self._io_type = 9  # TypeIrIo
        else:
            pass

        self._data_type = data_type

        self._id = (
            self._module_type
            + self._serial_number[2:9]
            + "-"
            + str(self._io_type)
            + "-"
            + str(self._io_offset)
        )

        if self._io_type == 8:  # "TypeSensorIo"
            # Keep the letter T or U
            self._raw_data = message[9:]
        elif self._io_type == 25:  # "TypeDmxIo"
            self._raw_data = message[12:]
        elif self._io_type == 29:  # "TypeDali"
            self._raw_data = message[13:]
        else:
            self._raw_data = message[10:]

        # Ignore unsupported io_type
        if self._io_type not in SUPPORTED_IO_TYPE_LIST:
            raise TypeError(f"Unsupported io type: {self._io_type}")

        self._data = self._parse_raw_data_legacy()
        self._status_requested = False

    def _parse_status_message(self, message: str):
        if is_clock_status(message):
            self._legacy = True
            self._parse_legacy_message(message)
        elif is_new_gen_status(message):
            self._legacy = False
            self._parse_newgen_message(message)
        else:
            self._legacy = True
            self._parse_legacy_message(message)


class LpCommand:
    def __init__(
        self,
        id: str,
        command_type: str,
        data: list | None = None,
        legacy: bool | None = None,
    ):
        self._id: str = id
        self._command_type: str = command_type.title()
        self._module_type: str = id[:3]

        # Formatting end_of_sn
        end_of_sn_hex = id[3:9]
        module_type_num = MODULE_TYPE_DICTIONNARY.get(self._module_type)["mod_type_num"]
        self._serial_number: str = module_type_num + end_of_sn_hex
        id_tab = id.split("-")
        self._data: list | None = data
        self._legacy: bool = is_legacy_module(self._module_type)

        if legacy is not None:
            self._legacy = legacy

        try:
            self._io_type = int(id_tab[1])
            self._io_offset = int(id_tab[2])
        except ValueError as ex:
            raise ValueError("Invalid id format") from ex

    @property
    def id(self) -> str:
        return self._id

    @property
    def serial_number(self) -> str:
        return self._serial_number

    @property
    def module_type(self) -> str:
        return self._module_type

    @property
    def io_type(self) -> int:
        return self._io_type

    @property
    def io_offset(self) -> int:
        return self._io_offset

    @property
    def data(self) -> list:
        return self._data

    @property
    def get_dict(self) -> dict:
        return self.__dict__

    def __str__(self):
        return 'LpCommand (Id: "{}", Serial Number: "{}", Module Type: "{}", Io Type: {} ({}), Io Offset: {}, Command Type: "{}", Data: {}, Legacy: {})'.format(
            self._id,
            self._serial_number,
            self._module_type,
            self._io_type,
            IO_TYPES_STRING.get(self._io_type, "TypeIoNotHandled"),
            self._io_offset,
            self._command_type,
            self._data,
            self._legacy,
        )

    def _get_legacy_message(self) -> str:
        cmd = str(cmd_type_legacy[self._command_type])
        io_num = self._io_offset

        # For TRV (TypeTrvIo or TypeTrvBtIo)
        if self._io_type in (6, 7):
            if self._io_offset <= 4:
                io_num = (self._io_offset * 2) - 1

        # For Dali (TypeDali)
        if self._io_type == 29:
            # io number is in 2 hex digits
            io_num = format(int(self._io_offset), "02X").upper()

        # For DISM20 (TypeInputIo)
        if self._io_type == 2:
            # io number is in hex format
            io_num = format(int(self._io_offset), "X").upper()

        legacy_base = self._id[:9] + "-" + str(io_num)

        # For SFE (SCENE -> TypeIoNotHandled),VAR, SYS, or MEM (GROUP)
        if self._io_type == 0 or self.module_type in ("VAR", "SYS", "MEM"):
            legacy_base = self._module_type + format(self._io_offset, "06X")
        else:
            legacy_base = self._id[:9] + "-" + str(io_num)

        if (
            self._command_type
            in (
                "Set Value",
                "Increase",
                "Decrease",
                "Set Mode Temperature",
                "Set Mode Regulation",
            )
        ) and self._data is not None:
            return legacy_base + cmd + str(self._data[0])
        elif self._command_type in ("Set Cooling Setpoint", "Set Heating Setpoint"):
            return legacy_base + cmd + f"{self._data[0]:.1f}"
        elif self._command_type == "Get Status":
            return legacy_base[:9] + "%S"
        else:
            return legacy_base + cmd

    def _get_newgen_message(self) -> str:
        try:
            sn_without_modtype = int(self._id[3:9], 16)
        except ValueError as ex:
            raise ValueError("Invalid id format") from ex

        if self._command_type == "Get Status":
            # /0/103 mean give all io status
            # return f"{self._module_type}/{sn_without_modtype}/{self._io_type}/0/103"
            return f"{self._module_type}/{sn_without_modtype}/{self._io_type}/{self._io_offset}/103"
        elif self._command_type == "Set Color":
            cmd = str(cmd_type_new_gen[self._command_type])

            if self._data is not None:
                cmd += "|" + "|".join(map(str, self._data))

            return f"{self._module_type}/{sn_without_modtype}/{self._io_type}/{self._io_offset}/{cmd}"
        else:
            cmd = str(cmd_type_new_gen[self._command_type])

            if self._data is not None:
                if isinstance(self._data[0], int):
                    cmd = cmd + "|" + str(self._data[0])
                elif isinstance(self._data[0], float):
                    cmd = cmd + "|" + f"{self._data[0]:.1f}"

            return f"{self._module_type}/{sn_without_modtype}/{self._io_type}/{self._io_offset}/{cmd}"

    def get_message(self) -> str:
        if self._legacy:
            return self._get_legacy_message()
        else:
            return self._get_newgen_message()


class LpAppInfo:
    def __init__(self, message: str):
        self._message: str = ""
        self._lp_version: str = "Unknown"
        self._lp_version_int: list = [0, 0, 0]
        self._charset = "UTF-8"
        self._name: str = "Unknown"  # Installation name
        self._ios_list: list = []  # Liste de dictonnaires représentant les ios

        # Clean message, remove caracters before "APPINFO" and after "END APPINFO"
        result = re.search(r"APPINFO(.*)END APPINFO", message, re.DOTALL)
        if result:
            self._message = result.group(1).strip()
            self._parse_appinfo()
        else:
            raise ValueError("Wrong APPINFO format")

    @property
    def name(self) -> str:
        return self._name

    @property
    def lp_version(self) -> str:
        return self._lp_version

    @property
    def lp_version_major(self) -> int:
        return self._lp_version_int[0]

    @property
    def lp_version_minor(self) -> int:
        return self._lp_version_int[1]

    @property
    def lp_version_revision(self) -> int:
        return self._lp_version_int[2]

    @property
    def charset(self) -> str:
        return self._charset

    @property
    def app_info(self) -> str:
        return self._message

    @property
    def ios(self) -> list:
        return self._ios_list

    def _get_next_lines(lines: list, current_index: int, nbr_of_lines: int):
        if current_index + nbr_of_lines <= len(lines):
            return lines[current_index + 1 : current_index + nbr_of_lines + 1]
        else:
            return lines[current_index + 1 :]

    def _parse_legacy_dmx_lines(self, lines: list[str]) -> dict | None:
        # Parse the first line
        result = self._parse_legacy_line(lines[0])
        extra_info_channels = []

        if result is None:
            return None

        nbr_of_channels = int(result["extra_info"][0])

        if len(lines) < nbr_of_channels + 1:
            return None

        for line in lines[1 : nbr_of_channels + 1]:
            channel_result = self._parse_legacy_line(line)

            if channel_result is None:
                continue

            # appinfo example : [R 0x00-0xFF]
            if channel_result["extra_info"] != []:
                extra_info_channels.append(channel_result["extra_info"][0])
            else:
                # Ignore DMX channel definition lines
                continue

        result["extra_info"] = extra_info_channels

        return {"nbr_of_channels": nbr_of_channels, "result": result}

    def _parse_legacy_line(self, line: str):
        module_type = line[:3].strip()
        serial_number: str = line[3:9]
        target_type: str | None = None
        io_offset: int = 0
        io_type: int = 0
        sw_version: str | None = None
        extra_info: str | None = None

        if module_type not in LEGACY_MODULE_TYPE_LIST:
            # "ZON", "TPR", "TPL", "STA", "CAM", "FRO", "RS2", "TSB" will be ignored too
            print("Not concerns a legacy module type, line ignored")
            return None

        # Extract extra informations
        pattern = r"\[(.*?)\]"
        # Search for all matches in the string
        extra_info = re.findall(pattern, line)[1:]

        # Extract installation informations
        installation_info = re.findall(pattern, line)[:][0]

        if module_type == "SFE":
            # ie: "SFE     1Sfeer 1-Scene 1[House||]"
            target_type = "scene"
            serial_number = "000000"
            io_type = 0  # TypeIoNotHandled
            io_offset = int(line[3:9], 16)
            io_name: str = line[9 : line.find("[")].strip()

        elif module_type == "VAR":
            # ie: "VAR     1boolMaster[Maison||][BOOL][MASTERONLY]"
            # ie: "VAR     3value[Maison||][VALU,00->80,LOOP]"
            target_type = "variable"
            serial_number = "000000"
            io_type = 16  # TypeVar
            io_offset = int(line[3:9], 16)
            io_name: str = line[9 : line.find("[")].strip()

        elif module_type == "SYS":
            # ie: "SYS     0Presence Simulation[Maison||][BOOL]"
            # ie: "SYS     9Day/Night[Maison||][BOOL][READONLY]"
            target_type = "variable"
            serial_number = "000000"
            io_type = 17  # TypeVarSys
            io_offset = int(line[3:9], 16)
            io_name: str = line[9 : line.find("[")].strip()

        elif module_type == "MEM":
            # ie: "MEM     1Group #1[House||][MIX][REF=BU4   EE4-5]"
            # ie: "MEM     2Group #2[House||][RGBW][REF=RW1/69/46/1]"
            # target_type = "group"
            serial_number = "000000"
            io_type = IOTYPE_OF_GROUP_CATEGORY.get(extra_info[0], 1)
            io_offset = int(line[3:9], 16)
            io_name: str = line[9 : line.find("[")].strip()

        elif module_type in ("QG1", "QG2", "NT1", "NT2", "RS2", "ET2"):
            # ie: "NT1000001[VERS=0x09]Module DNET01[House||]"
            # ie: "NT2000016[VERS=0x10]Module DNET02[Maison||]"
            # ie: "ET2    B6[VERS=0x0B]MOD DETH02[House||]
            # ie: "RS2     2[VERS=0x10]Interface protocole RS[House||]"
            target_type = None
            index_start_vers = line.find("[")
            index_end_vers = line.find("]")
            version_str = line[index_start_vers + 1 : index_end_vers]
            sw_version = str(int(version_str.split("=")[1], 16))
            io_name: str = line[
                index_end_vers + 1 : line.find("[", index_end_vers)
            ].strip()

            # Extract installation informations
            installation_info: str = line[
                line.find("[", index_end_vers) + 1 : line.find("]", index_end_vers + 1)
            ].strip()

            extra_info = []

        elif module_type == "I10":
            # Process extra_info
            # Extract the different parts of the line
            # Added From PROG M 39.1.0
            # Updated since PROG M version 43.4
            io_num_str = line[10]
            io_num = int(io_num_str)
            io_offset = 1
            io_name: str = line[11 : line.find("[")].strip()

            # Search paterne of analogic mode
            pattern = r"MIN=(.*)-MAX=(.*)-UNIT=(.*)"
            match = re.search(pattern, extra_info[0])

            if match:
                # Format: ["ANALOG-MIN=-10.5-MAX=120-UNIT=°C"]
                min_value = match.group(1)
                max_value = match.group(2)
                unit = match.group(3)
                probe_type = extra_info[0].split("-")[0]
                extra_info = [probe_type, min_value, max_value, unit]
                io_type = 21  # "TypeIn10VIo"
            elif len(extra_info) >= 2 and "LOCAL" in extra_info:
                # Format: ["NOLINK","LOCAL", "HMR=0xF0-HMT=0x00", "LHH=30.0-LHL=10.0-LCH=40.0-LCL=20.0-ISP=0.5"]
                # or      ["LOCAL", "HMR=0xF0-HMT=0x00", "LHH=30.0-LHL=10.0-LCH=40.0-LCL=20.0-ISP=0.5"]
                # if extra_info[1] == "LOCAL":
                #     extra_info = ["TEMP", extra_info[2], extra_info[3]]
                # else:
                #     extra_info = ["TEMP", extra_info[1], extra_info[2]]

                io_type = 8  # "TypeSensorsIo"
            else:
                # Wrong string format, default to analog
                extra_info = ["ANALOG", "0", "100", "V"]
                io_type = 21  # "TypeIn10VIo"

        elif module_type == "DAL":
            # ie: "DAL000010-01TL #12345678-1[House||][TYPE=TL]
            # ie: "DAL000010-02LED #87654321-2[House||][TYPE=LED]"
            # ie: "DAL000010-03PHASE #87654321-2[House||][TYPE=INCA]"
            target_type = "light"
            io_num_str = line[10] + line[11]
            io_name: str = line[12 : line.find("[")].strip()

            # Process extra_info
            pattern = r"=(.*)"
            match = re.search(pattern, extra_info[0])
            if match:
                extra_info = [match.group(1)]
            else:
                extra_info = ["TL"]

            # Determine the io offset and io type
            try:
                # Determine the io offset
                io_num = int(io_num_str, 16)

                io_offset = MODULE_TYPE_DICTIONNARY.get(module_type)["io_offsets"][
                    io_num - 1
                ]
                # Determine the io type
                io_type: int = MODULE_TYPE_DICTIONNARY.get(module_type)["io_types"][
                    io_num - 1
                ]
            except ValueError as ex:
                raise ValueError("Invalid io_offset format") from ex

        elif module_type == "DMX":
            # DMX    91-1DMX Output 1 RGBI[House||][4 CHANNELS]
            # DMX    91-1-CH1:Chan. R[R 0x00-0xFF]
            # DMX    91-1-CH2:Chan. G[G 0x00-0xFF]
            # DMX    91-1-CH3:Chan. B[B 0x00-0xFF]
            # DMX    91-1-CH4:Chan. I[I 0x00-0x64]
            target_type = "light"

            if extra_info != []:
                io_num_str = line[10]

                if line[11] == "-":
                    io_name: str = line[12 : line.find("[")].strip()
                else:
                    io_name: str = line[11 : line.find("[")].strip()

                nbr_of_channels = extra_info[0].split(" ")[0]
                extra_info = [nbr_of_channels]

                # Determine the io offset and io type
                try:
                    # Determine the io offset
                    io_num = int(io_num_str, 16)
                    io_offset = io_num

                    # Determine the io type
                    io_type: int = 25
                except ValueError as ex:
                    raise ValueError("Invalid io_offset format") from ex
            else:
                # Case of channel configuration line
                io_offset = line[14]
                io_name = ""
                extra_info = [installation_info]
                installation_info = "||"

        else:
            # ie: "BU4   EE4-1Entrée DPBU04 1[Maison||][PUSH=SHORT]"
            target_type = None

            # Extract the different parts of the line
            io_num_str = line[10]
            io_name: str = line[11 : line.find("[")].strip()

            # Ignore lines for pairs io num
            if (module_type in ("V24", "TRV", "TPV")) and ((int(io_num_str) % 2) == 0):
                return None

            # io_num must convert to shutter numbers
            if module_type in ("TPV", "TRV") and io_num_str != "1":
                io_num = int(io_num_str)  # 3,5,7  -> 2,3,4
                io_num_str = str((io_num + 1) // 2)

            # Determine the io offset and io type
            try:
                # Determine the io offset
                io_num = int(io_num_str, 16)
                io_offset = MODULE_TYPE_DICTIONNARY.get(module_type)["io_offsets"][
                    io_num - 1
                ]
                # Determine the io type
                io_type: int = MODULE_TYPE_DICTIONNARY.get(module_type)["io_types"][
                    io_num - 1
                ]
            except ValueError as ex:
                raise ValueError("Invalid io_offset format") from ex

            # Case of LT2 and LT4: not all io supported
            if module_type in ("LT2", "LT4"):
                if io_num in (7, 8, 9, 10, 15):
                    return None

            # Case of TypeInputIo: Convert extra_info into new gen format
            if module_type in BUTTONS_MODULE_TYPE_LIST:
                if io_type == 2:
                    if len(extra_info) >= 1:
                        match extra_info[0]:
                            case "PUSH=SHORT":
                                extra_info = ["1"]
                            case "PUSH=LONG":
                                extra_info = ["2"]
                            case _:  # "NOLINK"
                                extra_info = ["0"]
                    else:
                        extra_info = ["0"]

            # Case of Shutters:
            if module_type in SHUTTERS_MODULE_TYPE_LIST:
                # TODO At the moment there is no extra_info available
                pass

            # Case of typeSensorIo: Convert extra_info into new gen format
            if module_type in LEGACY_MODULE_WITH_TEMP_SENSOR_LIST:
                if io_type == 8:  # TypeSensorIo
                    # extra_info = ['NOLINK', 'LOCAL', 'HMR=0x70-HMT=0x00', 'LHH=30.0-LHL=10.0-LCH=40.0-LCL=20.0-ISP=0.5']
                    # or           ['LOCAL', 'HMR=0x70-HMT=0x00', 'LHH=30.0-LHL=10.0-LCH=40.0-LCL=20.0-ISP=0.5']
                    # newGen -> <regul_mask>|<temperature_mask>|<heat_limit_high>|<heat_limit_low>|<cool_limit_high>|<cool_limit_low>|<setpoint_step>
                    if len(extra_info) == 0:
                        extra_info = ["0"]
                    else:
                        exclusion_values = ["NOLINK", "LOCAL"]
                        local_extra_info = [
                            x for x in extra_info if x not in exclusion_values
                        ]
                        final_extra_info = []

                        # Extract regul. and temp. mask
                        mask_pattern = r"HMR=(\w+)-HMT=(\w+)"
                        match_mask = re.search(mask_pattern, local_extra_info[0])
                        if match_mask:
                            HMR = match_mask.group(1)
                            HMT = match_mask.group(2)
                            final_extra_info = [HMR, HMT]

                        # Extract data
                        # data_pattern = r"(LHH|LHL|LCH|LCL|ISP)=(\d+\.\d+)"
                        data_pattern = r"LHH=(\d+\.\d+)-LHL=(\d+\.\d+)-LCH=(\d+\.\d+)-LCL=(\d+\.\d+)-ISP=(\d+\.\d+)"
                        match_data = re.search(data_pattern, local_extra_info[1])

                        if match_data:
                            LHH, LHL, LCH, LCL, ISP = match_data.groups()
                            final_extra_info.extend([LHH, LHL, LCH, LCL, ISP])

                        link = None
                        if extra_info[1] == "LOCAL":
                            if extra_info[0] != "NOLINK":
                                link = extra_info[0]

                        extra_info = final_extra_info

                        if link:
                            extra_info.extend([link])

        # Ignore unsupported io_type
        if io_type not in SUPPORTED_IO_TYPE_LIST:
            return None

        # Format serial number
        serial_number_hex: str = serial_number.strip().lstrip("0").zfill(6).upper()
        module_type_num = MODULE_TYPE_DICTIONNARY.get(module_type)["mod_type_num"]
        full_serial_number: str = module_type_num + serial_number_hex

        # Endpoint Id construction
        endpoint_id: str = (
            module_type + serial_number_hex + "-" + str(io_type) + "-" + str(io_offset)
        )

        # Separate installation informations
        installation_name, floor_name, room_name = installation_info.split("|")

        # Determine target type
        if target_type is None:
            target_type = IO_DEFAULT_TARGET_TYPES.get(io_type, "unknown")

        # Create the dictionary
        result = {
            "id": endpoint_id,
            "module_type": module_type,
            "serial_number": full_serial_number,
            "io_type": io_type,
            "io_offset": io_offset,
            "io_name": io_name,
            "sw_version": sw_version,  # Not disponible in legacy
            "installation_name": installation_name,
            "floor_name": floor_name,
            "room_name": room_name,
            "extra_info": extra_info,
            "target_type": target_type,
        }

        return result

    def _parse_new_gen_line(self, line: str):
        extra_info: list[str] | None = None
        elements = line.split("/")

        if len(elements) < 7:
            return None

        # Extract the different parts of the line
        first_part, rest = elements[:7], elements[7:]

        (
            module_type,
            serial_number,
            io_type_str,
            io_offset_str,
            io_name,
            sw_version,
            installation_info,
        ) = first_part

        io_type = int(io_type_str)

        # Fixed a bug in older versions of LP
        # For DMOV06 and DMOV07 appinfo return TypeInputIo instead of TypeMovIo
        if module_type in ("MV6", "MV7") and io_type == 2:
            io_type_str = "34"  # TypeMovIo
            io_type = int(io_type_str)

        # Ignore unsupported io_type
        if io_type not in SUPPORTED_IO_TYPE_LIST:
            # print(f"Concerns an unsupported io type: '{io_type}', line ignored")
            return None

        if len(elements) == 8:
            # Each elements is separate by "|"
            sub_elements = [x for x in rest[0].split("|")]
            extra_info = sub_elements

        # Separate installation information
        info_list = installation_info.strip("[]").split("|")
        installation_name, floor_name, room_name = info_list

        # Format serial number
        serial_number_int = int(serial_number)
        serial_number_hex = hex(serial_number_int)[2:].zfill(6).upper()

        module_type_num = MODULE_TYPE_DICTIONNARY.get(module_type)["mod_type_num"]
        full_serial_number = module_type_num + serial_number_hex

        # Endpoint Id construction
        endpoint_id = (
            module_type + serial_number_hex + "-" + io_type_str + "-" + io_offset_str
        )

        # Determine target type
        target_type = IO_DEFAULT_TARGET_TYPES.get(int(io_type_str), "unknown")

        # Create the dictionary
        result = {
            "id": endpoint_id,
            "module_type": module_type,
            "serial_number": full_serial_number,
            "io_type": int(io_type_str),
            "io_offset": int(io_offset_str),
            "io_name": io_name,
            "sw_version": sw_version,
            "installation_name": installation_name,
            "floor_name": floor_name,
            "room_name": room_name,
            "extra_info": extra_info,
            "target_type": target_type,
        }

        return result

    def _parse_appinfo(self):
        # Extract and process APPINFO
        # ie: "(PROG M 40.0 00/00/00 00h00 Rev=3 CP=UTF-8) => MyHome :"
        print("Parsing APPINFO...")

        lines = self._message.splitlines()
        first_ligne = lines[0]  # Extract first line

        # Extract header
        result = re.search(r"\((.*?)\)", first_ligne)

        if result:
            header = result.group(1)
        else:
            raise ValueError("Wrong APPINFO format")

        regex = r"(?<=PROG\sM\s)(\d+\.\d+)(?:\s+.*?Rev=)(\d+)(?:\s+.*?CP=)([^\s]+)"
        match = re.search(regex, header)

        if match:
            version = match.group(1).strip()
            revision = match.group(2).strip()
            self._charset = match.group(3)
            self._lp_version = f"{version}.{revision}"
            version_parts = self._lp_version.split(".")
            if len(version_parts) == 3:
                self._lp_version_int = [int(item) for item in version_parts]
        else:
            raise ValueError("LP version not found")

        # Extract installation name
        result_name = re.search(r"=>(.*?):", first_ligne)

        if result_name:
            self._name = result_name.group(1).strip()
        else:
            self._name = "Unknown"

        # Extract IOs informations
        new_index = 0
        for index, line in enumerate(lines[1:]):
            # Skip lines
            if index < new_index:
                continue

            if line.startswith("END APPINFO"):
                break

            module_type = line[:3].strip()

            if module_type not in SUPPORTED_MODULE_TYPE_LIST:
                # TPR, TPL, STA, ZON, FRO, RS2, TSB are ingored too, because they are not module types
                continue

            # Try to parse line
            try:
                if module_type in LEGACY_MODULE_DMX_LIST:
                    dmx_result = self._parse_legacy_dmx_lines(lines[index + 1 :])

                    if dmx_result is not None:
                        # result = {"result": {...}, "nbr_of_channels": 3}
                        result = dmx_result["result"]
                        # Position the next loop after the DMX lines
                        new_index = index + 1 + dmx_result["nbr_of_channels"]
                    else:
                        result = None

                elif module_type in LEGACY_MODULE_TYPE_LIST:
                    result = self._parse_legacy_line(line)
                else:
                    result = self._parse_new_gen_line(line)

            except Exception as ex:
                print("An error occured during parse line:", line)
                print("Error:", ex)
                traceback.print_exc()
                result = None

            print("result:", result)  # TODO

            # Add IO
            if result is not None:
                if result["id"] not in set(element["id"] for element in self._ios_list):
                    self._ios_list.append(result)


def convert_legacy_to_new_gen(legacy_status: LpStatus) -> list[LpStatus] | None:
    """Convert legacy status data in new gen status if possible"""
    new_gen_status_list = []

    # newgen_status
    if legacy_status.is_legacy:
        return [legacy_status]

    if legacy_status.module_type in SHUTTERS_MODULE_TYPE_LIST:
        # "V24" (1 output), "TPV" (2 outputs), "TRV" (4 outputs)
        # V24 -> data = [a]
        # TPV -> data = [a,b]
        # TRV -> data = [a,b,c,d]
        # Convert legacy status data into newGen status data
        # legacy -> newGen
        #    0 (OFF)   ->    1 (Stopped last moving side unknown)
        #    1 (UP)    ->    2 (moving up)
        #    2 (DOWN)  ->    3 (moving down)
        #    3 (not possible) -> 0  (unknown state)

        status = copy.deepcopy(legacy_status)
        status._legacy = False

        for index, data in enumerate(legacy_status.data):
            # Convert into newGen representation
            status._data[index] = (data + 1) % 4

        new_gen_status_list.append(status)

    elif legacy_status.module_type == "DMV":
        # DMV -> data = [1, 0, 0] (speed, aux1, aux2)
        # speed -> TypeFanIo
        # aux1 -> TypeTorIo
        # aux2 -> TypeTorIo

        speed = legacy_status.data[0]
        aux_data = [legacy_status.data[1], legacy_status.data[2]]

        # TypeFanIo
        status_fan = copy.deepcopy(legacy_status)
        status_fan._legacy = False
        parts = legacy_status._id.rsplit("-", 1)  # DMV000001-13-1
        status_fan._io_type = 13  # TypeFanIo
        status_fan._io_offset = 1
        status_fan._id = parts[0] + "-1"
        status_fan._data = [speed]
        status_fan._raw_data = str(speed)

        new_gen_status_list.append(status_fan)

        # TypeTorIo
        for index, value in enumerate(aux_data):
            try:
                status = copy.deepcopy(legacy_status)
                status._legacy = False
                parts = legacy_status._id.rsplit("-", 2)
                status._io_type = 1  # TypeTorIo
                status._io_offset = index + 1
                status._id = parts[0] + "-1-" + str(status._io_offset)
                status._data = [value]
                status._raw_data = str(value)

                new_gen_status_list.append(status)
            except Exception as ex:
                print(
                    f"Error convert {legacy_status.module_type} legacy status into newGen for data[{index}]: {ex}"
                )
                continue

    elif legacy_status.module_type == "DMX":
        new_gen_status_list = [legacy_status]

    elif legacy_status.module_type in ("TE1", "TE2"):
        new_gen_status_list = [legacy_status]

    # BU1, BU2, BU4, BU6, BRT, PBL, PRL, BR2, BR4, B81, B82, B84, B86, BR6,
    # CL1, CL2, CL4, CL6, PRL
    elif legacy_status.module_type in BUTTONS_MODULE_TYPE_LIST:
        # on peut avoir du
        # TypeInputIo (on aura du 'I')
        # TypeLedIo, TypeLed8cIo (on aura du 'O')
        # TypeLedRgbIo, TypePbLcdIo (on aura du 'O')
        # TypeRgbwIo
        # TypeSensorIo (data_type = T or U)

        if legacy_status.io_type == 8:  # TypeSensorIo
            new_gen_status_list = [legacy_status]

        elif legacy_status.io_type == 2:  # TypeInputIo
            # newGen format
            # 0 -> Released
            # 1 -> Start of short push
            # 2 -> End of short push
            # 3 -> Start of long push
            # 4 -> End of long push
            # 5 -> Pressed

            # legacy format
            # 1 -> Pressed
            # 0 -> Released

            # extra_info = "PUSH=SHORT" or "PUSH=LONG" or "NOLINK" or empty or None
            # if extra_info == "PUSH=LONG":
            #     push = "long"
            # else:
            #     push = "short"

            status = copy.deepcopy(legacy_status)
            status._legacy = False

            for index, data in enumerate(legacy_status.data):
                # Convert into newGen representation
                status._data[index] = 5 if data == 1 else 0

            new_gen_status_list.append(status)

        elif legacy_status.io_type in (10, 15, 20, 60):
            legacy_status._legacy = False
            new_gen_status_list = [legacy_status]

        elif legacy_status.io_type == 9:  # TypeIrIo
            # Format: [key, push_state]
            status = copy.deepcopy(legacy_status)
            status._legacy = False
            status.data[0] = legacy_status.data[0]
            status.data[1] = 5 if status.data[0] != 0 else 0

            new_gen_status_list.append(status)

        elif legacy_status.io_type == 60:  # TypeLedRgbIo
            legacy_status._legacy = False
            new_gen_status_list = [legacy_status]

    # TODO LT2, LT4,
    else:
        legacy_status._legacy = False
        new_gen_status_list = [legacy_status]

    if len(new_gen_status_list) == 0:
        return None

    return new_gen_status_list
