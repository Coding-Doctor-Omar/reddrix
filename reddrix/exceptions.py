class FatalAntiBotBlockError(Exception):
    """Raised when the scraper is blocked after exhausting all attempts."""
    pass


class AntiBotBlockError(Exception):
    """Raised when the scraper is blocked once."""
    pass