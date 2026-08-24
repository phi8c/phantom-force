from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass
class UserDTO:
    """
    DTO tra ra NGOAI module user - khong bao gio de lot domain Entity User
    ra khoi module nay.
    """

    id: UUID

    email: str

    status: str

    full_name: str | None

    email_verified: bool