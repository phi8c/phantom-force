import asyncio
import hashlib
import secrets

from module.auth.domain.contracts.mfa_challenge_store import MfaChallengeStore
from module.auth.domain.value_objects.mfa_challenge import MfaChallenge


class InMemoryMfaChallengeStore(MfaChallengeStore):
    def __init__(self):
        self._challenges: dict[str, MfaChallenge] = {}
        self._lock = asyncio.Lock()

    async def create_challenge(self, challenge: MfaChallenge) -> str:
        raw_id = secrets.token_urlsafe(32)
        async with self._lock:
            self._remove_expired(challenge.created_at)
            self._challenges[self._hash(raw_id)] = challenge
        return raw_id

    async def take_challenge(self, challenge_id, now):
        async with self._lock:
            self._remove_expired(now)
            return self._challenges.pop(self._hash(challenge_id), None)

    def _remove_expired(self, now) -> None:
        expired = [
            key
            for key, challenge in self._challenges.items()
            if challenge.expires_at <= now
        ]
        for key in expired:
            self._challenges.pop(key, None)

    @staticmethod
    def _hash(raw_id: str) -> str:
        return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()
