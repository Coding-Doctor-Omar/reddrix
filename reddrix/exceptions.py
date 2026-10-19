class FatalAntiBotBlockError(Exception):
    """Raised when the scraper is blocked after exhausting all attempts."""
    pass


class AntiBotBlockError(Exception):
    """Raised when the scraper is blocked once."""
    pass

class NotInitializedError(Exception):
    """Raised when the scraper is used without being initialized."""
    pass

class InvalidRequestError(Exception):
    """Raised when the standalone get and post methods receive invalid requests."""
    pass