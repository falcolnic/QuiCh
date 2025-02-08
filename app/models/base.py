# Import all the models, so that Base has them before being
# imported by Alembic


from models.base_class import Base  # noqa
from models.texts import DocumentModel, TranscriptionModel  # noqa
from models.youtube import YoutubeModel  # noqa