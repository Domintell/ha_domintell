"""Domintell errors."""


class DomintellException(Exception):
    """Base exception for domintell."""


class MaxConnectedClient(DomintellException):
    """Max connected clients reached."""


class InvalidCredentials(DomintellException):
    """Username and or password is wrong."""


class SessionNotOpened(DomintellException):
    """Raised when we're trying to send commands until a session is opened."""


class UserDatabaseEmpty(DomintellException):
    """Raised when we're trying to connect in while there is no user account configured."""


class GatewaySoftwareOutdated(DomintellException):
    """Raised when the gateway version of the gateway is (too) outdated."""


class LpVersionUnsupported(DomintellException):
    """Raised when the Lightprotocol version of the gateway is unsupported."""


class InvalidAppinfo(DomintellException):
    """Raised when the appinfo format is invalid."""


class ModuleTypeNotSupported(DomintellException):
    """Module type is not supported."""


class IoTypeNotSupported(DomintellException):
    """IO type is not supported."""
