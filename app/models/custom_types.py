import uuid

from sqlalchemy import BLOB, TypeDecorator


class UUID_as_Integer(TypeDecorator):
    impl = BLOB
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert UUID to integer before storing in the database."""
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value.bytes
        return uuid.UUID(value).bytes

    def process_result_value(self, value, dialect):
        """Convert integer back to UUID after retrieving from the database."""
        if value is None:
            return None
        return uuid.UUID(bytes=value)
