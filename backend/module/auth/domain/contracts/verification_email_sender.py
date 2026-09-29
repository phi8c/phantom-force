from abc import ABC, abstractmethod


class VerificationEmailSender(ABC):
    @abstractmethod
    async def send_verification_email(
        self,
        recipient: str,
        raw_token: str,
    ) -> None:
        pass
