from typing import Any

from sqlalchemy.orm import as_declarative


@as_declarative()
class Base:
    id: Any

    def dict(self):
        """Returns a dict representation of a model."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}