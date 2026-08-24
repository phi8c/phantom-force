from __future__ import annotations

from datetime import datetime
from datetime import timedelta

IDLE_TIMEOUT_MINUTES = 30
ABSOLUTE_TIMEOUT_HOURS = 12


class SessionExpiryPolicy:
    """
    2 lop timeout doc lap: idle (khong hoat dong) va absolute (tuyet doi
    ke ca dang hoat dong lien tuc) - chuan banking-grade da chot tu dau.
    """

    def compute_idle_expiry(
        self,
        now: datetime,
    ) -> datetime:

        return now + timedelta(
            minutes=IDLE_TIMEOUT_MINUTES,
        )

    def compute_absolute_expiry(
        self,
        now: datetime,
    ) -> datetime:

        return now + timedelta(
            hours=ABSOLUTE_TIMEOUT_HOURS,
        )