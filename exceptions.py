class NotForSending(Exception):
    pass


class ProblemDescriptions(Exception):
    pass


class InvalidResponseCode(Exception):
    pass


class ConnectingError(Exception):
    pass


class EmptyResponseFromAPI(NotForSending):
    pass


class TelegramError(NotForSending):
    pass


class APIResponseError(Exception):
    pass


class InvalidResponseFormat(Exception):
    pass


class MessageNotSend(Exception):
    pass


class MissingCurrentDateError(KeyError):
    pass