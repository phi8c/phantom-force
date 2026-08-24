from enum import Enum


class PolicyOperator(str, Enum):
    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    GTE = "gte"
    LTE = "lte"
    CONTAINS = "contains"