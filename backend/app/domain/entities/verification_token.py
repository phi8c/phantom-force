from dataclasses import dataclass
from datetime import datetime

from app.domain.enums.token_purpose import TokenPurpose


@dataclass
class VerificationToken:

    id: str

    user_id: str

    token_hash: str

    purpose: TokenPurpose

    expires_at: datetime

    used_at: datetime | None

    created_at: datetime