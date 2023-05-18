class NotForSending(Exception):
    pass


class InvalidResponseCode(Exception):
    pass


class ConnectingError(Exception):
    pass


class InvalidResponseFormat(Exception):
    pass


class MissingCurrentDateError(NotForSending):
    pass


class CurrentDateError(NotForSending):
    pass