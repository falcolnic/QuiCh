# Import all the models, so that Base has them before being
# imported by Alembic


from app.models.base_class import Base  # noqa
from app.models.search import SearchModel  # noqa
from app.models.texts import (  # noqa
    DocumentModel,
    IdeaModel,
    TranscriptionModel,
    YoutubeModel,
)
