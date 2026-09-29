from __future__ import annotations

from datetime import datetime
from datetime import timedelta

class SessionExpiryPolicy:
    """
    2 lop timeout doc lap: idle (khong hoat dong) va absolute (tuyet doi
    ke ca dang hoat dong lien tuc) - chuan banking-grade da chot tu dau.
    """

    def compute_idle_expiry(
        self,
        now: datetime,
        timeout_minutes: int,
    ) -> datetime:

        return now + timedelta(
            minutes=timeout_minutes,
        )

    def compute_absolute_expiry(
        self,
        now: datetime,
        timeout_minutes: int,
    ) -> datetime:

        return now + timedelta(
            minutes=timeout_minutes,
        )

    def refresh_idle_expiry(
        self,
        now: datetime,
        previous_last_seen_at: datetime,
        previous_idle_expires_at: datetime,
    ) -> datetime:
        return now + (previous_idle_expires_at - previous_last_seen_at)
