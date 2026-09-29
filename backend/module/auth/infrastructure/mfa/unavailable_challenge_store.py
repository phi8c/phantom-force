from module.auth.domain.contracts.mfa_challenge_store import MfaChallengeStore
from module.auth.domain.value_objects.mfa_challenge import MfaChallenge


class UnavailableMfaChallengeStore(MfaChallengeStore):
    async def create_challenge(self, challenge: MfaChallenge) -> str:
        raise RuntimeError("MFA challenge store has not been configured")

    async def take_challenge(self, challenge_id, now):
        raise RuntimeError("MFA challenge store has not been configured")
