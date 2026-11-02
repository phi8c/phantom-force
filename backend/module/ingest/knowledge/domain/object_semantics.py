import re
import unicodedata

from module.ingest.knowledge.domain.entities import KnowledgeObject


EMBEDDING_TEXT_VERSION = "entity-v1"


def normalize_entity_text(value: str | None) -> str:
    if not value:
        return ""
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", ascii_value.lower()))


def object_embedding_text(entity: KnowledgeObject) -> str:
    name = entity.object_name or entity.identifier_name or entity.identifier_code or entity.object_code
    return f"entity type: {entity.object_code}; entity name: {name}"


def identifier_embedding_text(entity: KnowledgeObject) -> str | None:
    value = entity.identifier_name or entity.identifier_code
    if not value:
        return None
    return f"entity type: {entity.object_code}; identifier: {value}"
