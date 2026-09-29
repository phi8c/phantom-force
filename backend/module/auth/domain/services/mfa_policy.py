from datetime import datetime, timedelta


MFA_CHALLENGE_TTL = timedelta(minutes=5)


class MfaPolicy:
    @staticmethod
    def is_required(policy_requires_mfa: bool, user_has_mfa: bool) -> bool:
        return policy_requires_mfa or user_has_mfa

    @staticmethod
    def enrollment_is_required(
        policy_requires_mfa: bool,
        user_has_mfa: bool,
    ) -> bool:
        return policy_requires_mfa and not user_has_mfa

    @staticmethod
    def challenge_expires_at(now: datetime) -> datetime:
        return now + MFA_CHALLENGE_TTL
