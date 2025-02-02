import logging

log = logging.getLogger(__name__)


def embed(client, text):
    log.info("Creating embeddings for text: %s", text)
    embedding = client.embed([text], model="voyage-3-lite")
    return embedding.embeddings[0]