from datetime import datetime, timedelta


class ReauthenticationPolicy:
    @staticmethod
    def is_recently_authenticated(
        authenticated_at: datetime,
        now: datetime,
        reauthentication_minutes: int | None,
    ) -> bool:
        if reauthentication_minutes is None:
            return True
        if reauthentication_minutes <= 0:
            return False
        return authenticated_at + timedelta(minutes=reauthentication_minutes) > now
