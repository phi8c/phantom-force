from enum import Enum


class KnowledgeFieldDataType(
    Enum,
):
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    OBJECT = "object"
    ARRAY = "array"
    MEASUREMENT = "measurement"
