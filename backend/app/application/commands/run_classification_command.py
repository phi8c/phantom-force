from dataclasses import dataclass
from uuid import UUID

from app.application.commands.base_command import BaseCommand


@dataclass(slots=True)
class RunClassificationCommand(BaseCommand):
    document_id: UUID
    batch_id: UUID