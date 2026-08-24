from dataclasses import dataclass
from typing import Any

from app.domain.enums.policy_operator import PolicyOperator


@dataclass
class PolicyCondition:

    id: str

    policy_id: str

    attribute_path: str

    operator: PolicyOperator

    value: Any
    
    
    
    
    