from app.application.commands.run_classification_command import (
    RunClassificationCommand,
)
from app.application.commands.run_embedding_command import (
    RunEmbeddingCommand,
)

from app.shared.config.settings import settings


QUEUE_MAPPING = {

    RunClassificationCommand:
        settings.AZURE_SB_QUEUE_CLASSIFICATION,

    RunEmbeddingCommand:
        settings.AZURE_SB_QUEUE_EMBEDDING,

}