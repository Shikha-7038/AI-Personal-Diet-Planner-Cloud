"""Exceptions shared by the cloud (database / storage) layer."""


class CloudServiceError(Exception):
    """A cloud service (database or object storage) failed or is unreachable."""


class DuplicateEmailError(Exception):
    """Raised when registering an e-mail address that already exists."""
