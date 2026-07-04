class TwitterBotError(Exception):
    """Base error for all Twitter Bot failures."""


class AuthError(TwitterBotError):
    """Raised when credential verification fails or the user is not logged in."""


class ApiAccessError(TwitterBotError):
    """Raised when the X API rejects a call due to an insufficient access tier."""


class RateLimitError(TwitterBotError):
    """Raised when the X API rate limit is hit."""
