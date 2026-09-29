from __future__ import annotations

from datetime import datetime, timezone

from module.auth.domain.contracts.clock import (
    Clock,
)


class SystemClock(
    Clock,
):
    """
    Impl that dung production - fake_clock.py (test double) se nam o
    tests/, khong lam bay gio de giu scope dung persistence+application.
    """

    def now(
        self,
    ) -> datetime:

        return datetime.now(timezone.utc)
