from __future__ import annotations

from datetime import datetime

from module.auth.domain.services.clock import (
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

        return datetime.utcnow()