from pydantic import BaseModel


class Search(BaseModel):
    search: str