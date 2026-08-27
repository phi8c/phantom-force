from dataclasses import dataclass
from typing import Self


@dataclass(slots=True)
class SectionNode:

    id: str

    title: str

    level: int

    content: str

    children: list[Self]

    token_count: int

    descendant_token_count: int