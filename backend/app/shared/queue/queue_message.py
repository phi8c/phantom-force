from dataclasses import dataclass
from typing import Any


@dataclass
class QueueMessage:

    queue_name: str

    payload: Any