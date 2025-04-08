from typing import List

from pydantic import BaseModel


class DocumentSchema(BaseModel):
    title: str
    context: str
    start: int
    end: int


class DocumentListSchema(BaseModel):
    docs: List[DocumentSchema]
