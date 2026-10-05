import logging
from urllib.parse import urlencode

from module.auth.domain.contracts.verification_email_sender import (
    VerificationEmailSender,
)
from module.auth.domain.exception.exceptions import VerificationDeliveryError


logger = logging.getLogger(__name__)


class ConsoleVerificationEmailSender(VerificationEmailSender):
    def __init__(self, verification_url: str | None):
        self._verification_url = verification_url

    async def send_verification_email(
        self,
        recipient: str,
        raw_token: str,
    ) -> None:
        if not self._verification_url:
            raise VerificationDeliveryError(
                "Verification URL has not been configured"
            )

        separator = "&" if "?" in self._verification_url else "?"
        verification_link = (
            f"{self._verification_url}{separator}"
            f"{urlencode({'token': raw_token})}"
        )
        logger.warning(
            "[AUTH_CONSOLE_EMAIL] recipient=%s verification_link=%s",
            recipient,
            verification_link,
        )
