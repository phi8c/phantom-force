from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from module.auth.domain.value_objects.mfa_challenge import MfaChallenge


class MfaChallengeStore(ABC):
    @abstractmethod
    async def create_challenge(self, challenge: MfaChallenge) -> str:
        pass

    @abstractmethod
    async def take_challenge(
        self,
        challenge_id: str,
        now: datetime,
    ) -> MfaChallenge | None:
        pass
