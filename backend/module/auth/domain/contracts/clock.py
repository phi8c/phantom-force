from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from datetime import datetime


class Clock(
    ABC,
):
    """
    Tru tuong hoa "thoi diem hien tai" - use case KHONG bao gio goi
    datetime.utcnow() truc tiep, luon xin qua Clock. Nho vay unit test co
    the fake thoi gian (vd "gia su da qua 31 phut") ma khong can sleep that
    hay monkeypatch datetime module.
    """

    @abstractmethod
    def now(
        self,
    ) -> datetime:
        pass