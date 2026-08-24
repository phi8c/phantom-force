from app.application.commands.run_classification_command import (
    RunClassificationCommand,
)
from app.application.commands.run_embedding_command import (
    RunEmbeddingCommand,
)

COMMAND_REGISTRY = {
    RunClassificationCommand.__name__: RunClassificationCommand,
    RunEmbeddingCommand.__name__: RunEmbeddingCommand,
}