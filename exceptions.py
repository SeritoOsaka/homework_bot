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
