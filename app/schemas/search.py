from uuid import UUID

from pydantic import BaseModel


class Search(BaseModel):
    search: str


class SearchLogSchema(BaseModel):
    id: UUID
    question: str
    response: str
