from dataclasses import dataclass
from datetime import datetime

from app.domain.enums.user_status import UserStatus


@dataclass
class User:

    id: str

    email: str

    status: UserStatus

    full_name: str | None

    email_verified_at: datetime | None

    created_at: datetime

    updated_at: datetime

    deleted_at: datetime | None