from enum import Enum


class AuthenticationContextType(str, Enum):
    MANAGEMENT = "MANAGEMENT"
    KNOWLEDGE_SPACE = "KNOWLEDGE_SPACE"
