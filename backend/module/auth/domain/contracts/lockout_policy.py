from __future__ import annotations

from datetime import datetime
from datetime import timedelta

MAX_ATTEMPTS_BEFORE_LOCK = 5
BASE_LOCK_MINUTES = 15


class LockoutPolicy:
    """
    Pure logic - khong dung repository, khong dung DB. Test khong can mock gi.
    """

    def is_locked(
        self,
        locked_until: datetime | None,
        now: datetime,
    ) -> bool:

        return locked_until is not None and locked_until > now

    def next_lock_duration(
        self,
        failed_attempts: int,
    ) -> timedelta | None:

        if failed_attempts < MAX_ATTEMPTS_BEFORE_LOCK:
            return None

        multiplier = 2 ** (failed_attempts - MAX_ATTEMPTS_BEFORE_LOCK)

        return timedelta(
            minutes=BASE_LOCK_MINUTES * multiplier,
        )