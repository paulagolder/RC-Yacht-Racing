"""errors.py - the error raised when a file cannot be read or written."""


class StorageError(Exception):
    """A file could not be read or written. The message is safe to show the user."""
