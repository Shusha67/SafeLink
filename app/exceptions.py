class SafeLinkError(Exception):
    pass


class CheckError(SafeLinkError):
    """A security check failed to execute (not the same as a negative finding)."""
    pass


class CacheError(SafeLinkError):
    """Cache read/write failure."""
    pass


class MessagingError(SafeLinkError):
    """Messaging platform communication failure."""
    pass
