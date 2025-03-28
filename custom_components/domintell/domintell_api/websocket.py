import asyncio
import ssl
import re
import enum

from collections.abc import Callable
import hashlib
import logging

import websockets

from .const import SUPPORTED_MODULE_TYPE_LIST
from .errors import (
    MaxConnectedClient,
    InvalidCredentials,
    SessionNotOpened,
    UserDatabaseEmpty,
)
from .lightprotocol import (
    LpStatus,
    LpCommand,
    is_hour_message,
    convert_legacy_to_new_gen,
)


# Create SSL context without certificate verification
ssl_context = ssl.SSLContext()
ssl_context.verify_mode = ssl.CERT_NONE


class ConnectionState(enum.Enum):
    """States of the websocket connection."""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTED = "reconnected"
    LOGGED = "logged"
    RELOGGED = "relogged"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


def clean_appinfo(message: str):
    """Remove unwanted informations from APPINFO message."""
    result = re.search(r"APPINFO(.*)END APPINFO", message, re.DOTALL)

    if result:
        return result.group(0).strip()

    return None


def parse_lp_version(message: str) -> str | None:
    """Extract lightprotocol version from message."""
    # ie: "INFO:LPVER=43.7.1:INFO"
    result = re.search(r"INFO:LPVER=(.*):INFO", message.strip(), re.DOTALL)

    if result:
        return result.group(1).strip()

    return None


def parse_discover(message: str) -> dict | None:
    """Extract gateway informations from message."""
    # ie: "INFO:I AM A DGQG04-192.168.1.250-169.254.162.138-17481-54000001-WSS:INFO"
    # ie  "INFO:I AM A DNET02-10.0.3.25-169.254.126.251-17481-5d000093-WSS:INFO"
    # ie  "INFO:I AM A DNET02-0-169.254.126.251-17481-5d000093-WSS:INFO"
    regex = r"^INFO:I AM A\s+.*:INFO$"
    match = re.match(regex, message)

    if match:
        try:
            parts = message.strip().split("-")
            if len(parts) >= 5:
                module_ip: str = parts[1] if parts[1] != "0" else parts[2]
                serial_number: str = parts[4].upper()  # id: "54000001"
                model: str = parts[0].rsplit(" ", 1)[1]  # "DGQG04"
                module_number: int = int(serial_number[3:])  # 1
                name: str = model + "-" + str(module_number)  # "DGQG04-1"
                return {
                    "id": serial_number,
                    "serial_number": serial_number,
                    "serial_number_text": name,
                    "model": model.upper(),
                    "name": name.upper(),
                    "ip": module_ip,
                }
        except Exception as ex:
            print("Error parsing websocket server info:", ex)

    return None


class DomintellClient:
    def __init__(
        self,
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._logger = logging.getLogger(f"{__package__}[{host}]")
        self._host: str = host
        self._port: int = port
        self._username: str = username or ""
        self._password: str = password or ""
        self._nonce: str | None = None
        self._salt: str | None = None
        self._websocket = None
        self._is_connected: bool = False
        self._is_reconnected: bool = False
        self._is_session_opened: bool = False
        self._connect_attempts: int = 0
        self._on_connection_state_change = None
        self._on_message: Callable[[str], None] = None
        self._on_status: Callable[[list[LpStatus]], None] = None
        self._on_appinfo: Callable[[str], None] = None
        self._keep_alive_task = None
        self._listen_task = None
        self._lp_version: str | None = None
        self._server_info: dict | None = None
        self._exit_on_error: bool = False

    @property
    def host(self) -> str:
        """Return the hostname."""
        return self._host

    @property
    def port(self) -> int:
        """Return the port."""
        return self._port

    @property
    def is_connected(self) -> bool:
        return self._is_connected and self._is_session_opened

    @property
    def is_session_opened(self) -> bool:
        return self._is_session_opened

    @property
    def lp_version(self) -> str | None:
        """Return the Lightprotocol version."""
        return self._lp_version

    @property
    def server_info(self) -> dict | None:
        """Return the gateway informations."""
        return self._server_info

    async def test_connection(self, host, port) -> None:
        """Just test websocket connection"""

        try:
            self._websocket = await websockets.connect(
                f"wss://{host}:{port}", ssl=ssl_context
            )

            response = await self._websocket.recv()

            if "ERROR:Max connected clients reached:ERROR" in response:
                raise MaxConnectedClient("Max connected clients reached")

        except websockets.exceptions.ConnectionClosedError as ex:
            # From LP version 42.9.0
            if ex.reason == "ERROR:Max connected clients reached:ERROR":
                raise MaxConnectedClient("Max connected clients reached") from ex

            raise ConnectionError(str(ex)) from ex

        except Exception as ex:
            raise type(ex)(ex) from ex
        finally:
            if self._websocket is not None:
                await self._websocket.close()

    async def connect(self, exit_on_error: bool = False) -> None:
        """Start websocket connection."""
        self._exit_on_error = exit_on_error
        self._is_connected = False
        self._is_reconnected = False
        self._is_session_opened = False

        try:
            self._connect_attempts += 1

            if self._connect_attempts == 1:
                self._logger.info("Connection...")
            else:
                self._logger.info("Retry Connection...")

            self._emit(ConnectionState.CONNECTING)
            self._websocket = await websockets.connect(
                f"wss://{self._host}:{self._port}", ssl=ssl_context
            )

            if self._connect_attempts == 1:
                self._is_reconnected = False
                self._emit(ConnectionState.CONNECTED)
            else:
                self._is_reconnected = True
                self._emit(ConnectionState.RECONNECTED)

            self._is_connected = True

            self._logger.info(f"Connected to {self.host}")
            self._logger.debug("Login...")

            response = await self._websocket.recv()

            if "ERROR:Max connected clients reached:ERROR" in response:
                await self.disconnect()
                raise MaxConnectedClient("Max connected clients reached")

            # INFO:Waiting for LOGINPSW:NONCE=8547165051709890817:INFO
            if "INFO:Waiting for LOGINPSW:NONCE=" in response:
                hashed_final = ""
                # Logging in requires a username and password
                pattern = r"NONCE=(.*?):"
                self._nonce = re.findall(pattern, response)[0]

                # Request salt for specified user
                self._logger.debug("Request salt...")
                await self._websocket.send("REQUESTSALT@" + self._username)

                response = await self._websocket.recv()
                # response : "INFO:REQUESTSALT:USERNAME=toto:NONCE=9301906811536867321:SALT=1007182019:INFO"
                if "INFO:REQUESTSALT:USERNAME=" in response:
                    # Extract NONCE
                    pattern_nonce = r"NONCE=(.*?):"
                    self._nonce = re.findall(pattern_nonce, response)[0]

                    # Extract SALT
                    pattern_salt = r"SALT=(.*?):"
                    self._salt = re.findall(pattern_salt, response)[0]

                    if self._salt != "":
                        self._logger.debug("Compute token...")
                        salted_password = (self._password + self._salt).encode("utf-8")

                        # Hash the salted password
                        sha512 = hashlib.sha512()
                        sha512.update(salted_password)
                        hashed_salted_password = sha512.hexdigest()
                        tmp = (hashed_salted_password + self._nonce).encode("utf-8")
                        sha512 = hashlib.sha512()
                        sha512.update(tmp)
                        hashed_final = sha512.hexdigest()
                    else:
                        hashed_final = ""

                # Logging
                await self._websocket.send(
                    "LOGINPSW@" + self._username + ":" + hashed_final
                )

                response = await self._websocket.recv()

            # expected response: "INFO:Session opened:INFO"
            if "INFO:Session opened:INFO" in response:
                self._connect_attempts = 1  # reset on successful logged in
                self._is_session_opened = True

                # Request Lightprotocol version and gateway informations
                await self.request_lp_version()
                await self.request_discover()

                if self._is_reconnected:
                    self._emit(ConnectionState.RELOGGED)
                    self._logger.info(f"Session reopened to {self.host}")
                else:
                    self._emit(ConnectionState.LOGGED)
                    self._logger.info(f"Session opened to {self.host}")
            elif "ERROR:Invalid credentials:ERROR" in response:
                raise InvalidCredentials("Invalid credentials")
            elif "ERROR:User database empty" in response:
                raise UserDatabaseEmpty("No user account in database")
            elif "ERROR:Invalid command" in response:
                # Should never happen
                raise SessionNotOpened("Session not opened")
            else:
                raise ConnectionError("Unable to open session")

            # Create a task to keep connection alive
            self._keep_alive_task = asyncio.create_task(self._keep_alive())

            # Create a task for listening to messages
            self._listen_task = asyncio.create_task(self._listen_for_messages())

        except (InvalidCredentials, UserDatabaseEmpty) as ex:
            await self.disconnect()
            raise type(ex)(str(ex))

        except websockets.exceptions.ConnectionClosedError as ex:
            # From LP version 42.9.0
            await self.disconnect()

            if ex.reason == "ERROR:Invalid credentials:ERROR":
                raise InvalidCredentials("Invalid credentials") from ex
            elif ex.reason == "ERROR:Max connected clients reached:ERROR":
                raise MaxConnectedClient("Max connected clients reached") from ex
            elif ex.reason == "INFO:Session timeout:INFO":
                raise TimeoutError(ex) from ex
            elif "ERROR:Invalid command" in ex.reason:
                raise SessionNotOpened("Session not opened") from ex
            else:
                raise ConnectionError(str(ex)) from ex

        except Exception as ex:
            # Possible errors:
            #   InvalidCommand
            #   TimeoutError
            #   ConnectionRefusedError
            #   socket.gaierro: "[Errno 11001] getaddrinfo failed"
            #   [Errno 111] Connect call failed
            #   [Errno -5] Name has no usable address
            #   [Errno -2] Name does not resolve
            #   [Errno 22] Invalid argument
            #   All other

            await self.disconnect()

            if self._exit_on_error:
                if str(ex) in (
                    "[Errno 11001] getaddrinfo failed",
                    "[Errno -5] Name has no usable address",
                    "[Errno -2] Name does not resolve",
                ):
                    raise TimeoutError(ex) from ex
                else:
                    text = str(ex) or "unknown_error"
                    raise type(ex)(text) from ex
            else:
                self._logger.warning(
                    f"The connection attempt on the gateway failed - Reason : {ex}"
                )
                await self._reconnect()

    async def disconnect(self) -> None:
        """Close websocket connection."""
        if self._listen_task is not None:
            # Stop the reception task
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

            self._listen_task = None

        if self._keep_alive_task is not None:
            # Stop the keep alive task
            self._keep_alive_task.cancel()
            try:
                await self._keep_alive_task
            except asyncio.CancelledError:
                pass

            self._keep_alive_task = None

        if self._websocket is not None:
            previous_state = self.is_connected

            if self.is_connected:
                self._is_connected = False
                self._is_reconnected = False
                self._emit(ConnectionState.DISCONNECTING)

            self._is_session_opened = False

            await self._websocket.close()
            self._websocket = None

            if previous_state == True:  # pylint: disable=C0121
                self._emit(ConnectionState.DISCONNECTED)

    def on_connection_state_change(self, callback) -> None:
        self._on_connection_state_change = callback

    def on_message(self, callback: Callable[[str], None]) -> None:
        self._on_message = callback

    def on_status(self, callback: Callable[[LpStatus], None]) -> None:
        self._on_status = callback

    def on_appinfo(self, callback: Callable[[str], None]) -> None:
        self._on_appinfo = callback

    def _emit(self, state: ConnectionState) -> None:
        if self._on_connection_state_change is not None:
            self._on_connection_state_change(state)

    async def send_command(self, cmd: LpCommand) -> None:
        if self.is_session_opened:
            self._logger.debug("Send command: {cmd}")
            try:
                await self.send_message(cmd.get_message() + "\r\n")
            except Exception as ex:
                self._logger.error(f"Error sending command: {ex}")

    async def send_message(self, message: str) -> None:
        if self.is_session_opened:
            self._logger.debug(f"Send message: {message}")
            try:
                await self._websocket.send(message)
            except Exception as ex:
                self._logger.error(f"Error sending message: {ex}")

    async def request_appinfo(self) -> None:
        if self.is_session_opened:
            try:
                await self._websocket.send("APPINFO\r\n")
            except Exception as ex:
                self._logger.error(f"Error sending APPINFO message: {ex}")

    async def request_lp_version(self) -> None:
        """Disponible from Lightprotocol version 43.7.0"""
        if self.is_session_opened:
            try:
                await self._websocket.send("GETLPVER\r\n")
            except Exception as ex:
                self._logger.error(f"Error sending GETLPVER message: {ex}")

    async def request_discover(self) -> None:
        """Disponible from Lightprotocol version 43.7.0"""
        if self.is_session_opened:
            try:
                await self._websocket.send("DISCOVER\r\n")
            except Exception as ex:
                self._logger.error(f"Error sending DISCOVER message: {ex}")

    async def request_all_status(self) -> None:
        if self.is_session_opened:
            try:
                await self._websocket.send("PING\r\n")
            except Exception as ex:
                self._logger.error(f"Error sending PING message: {ex}")

    def _on_lp_version(self, message: str) -> None:
        self._lp_version = parse_lp_version(message)
        print("LP Version:", self._lp_version)

    def _on_discover_message(self, message: str) -> None:
        self._server_info = parse_discover(message)
        print("Client info:", self._server_info)

    async def _listen_for_messages(self) -> None:
        while True:
            try:
                message = await self._websocket.recv()
                if message is None:
                    continue

                conditions = [
                    "INFO:" not in message,
                    "APPINFO" not in message,
                    "PONG" not in message,
                    not message.startswith("INFO:"),
                    "disconnected" not in message,
                    "connected" not in message,
                    "{" not in message,  # voice info
                ]

                if all(conditions) and self._on_message:
                    self._on_message(message)

                if all(conditions) and not is_hour_message(message) and self._on_status:
                    # The message may contain multiple lines
                    lines = message.splitlines()
                    lp_status_list = []

                    for line in lines[:]:
                        try:
                            if line[:3] in SUPPORTED_MODULE_TYPE_LIST:
                                new_status = LpStatus(line)

                                # Convert status in new_gen if necessary
                                if new_status.is_legacy:
                                    new_gen_status_list = convert_legacy_to_new_gen(
                                        new_status
                                    )

                                    if new_gen_status_list is not None:
                                        lp_status_list.extend(new_gen_status_list)

                                else:
                                    # Is a newGen status
                                    lp_status_list.append(new_status)

                        except Exception as ex:
                            self._logger.error(f"Error parsing status message: {ex}")

                    if len(lp_status_list) > 0:
                        self._on_status(lp_status_list)

                    continue

                if message.startswith("INFO:LPVER="):
                    self._on_lp_version(message)
                    continue

                if message.startswith("INFO:I AM A"):
                    self._on_discover_message(message)
                    continue

                if message.startswith("APPINFO") and self._on_appinfo:
                    appinfo = clean_appinfo(message)
                    if appinfo is not None:
                        await self._on_appinfo(appinfo)
                        continue

            except Exception as ex:
                self._logger.error(f"Error receiving message: {ex}")
                await self.disconnect()
                await self._reconnect()
                break

    async def _keep_alive(self, seconds: int = 40):
        while True:
            await asyncio.sleep(seconds)
            if self.is_connected:
                await self.send_message("HELLO\r\n")

    async def _reconnect(self) -> None:
        """Retry to connect to Domintell bridge."""
        reconnect_wait = min(2 * self._connect_attempts, 30)
        # every 10 failed connect attempts log warning
        if self._connect_attempts % 10 == 0:
            self._logger.warning(
                "%s Attempts to (re)connect to gateway failed"
                " - This might be an indication of connection issues.",
                self._connect_attempts,
            )
        await asyncio.sleep(reconnect_wait)
        await self.connect()
