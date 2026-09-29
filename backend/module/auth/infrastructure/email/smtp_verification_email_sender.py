from __future__ import annotations

import asyncio
from email.message import EmailMessage
import smtplib
from urllib.parse import urlencode

from module.auth.domain.contracts.verification_email_sender import (
    VerificationEmailSender,
)
from module.auth.domain.exception.exceptions import VerificationDeliveryError


class SmtpVerificationEmailSender(VerificationEmailSender):
    def __init__(
        self,
        host: str | None,
        port: int,
        username: str | None,
        password: str | None,
        sender: str | None,
        verification_url: str | None,
        use_tls: bool,
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._sender = sender
        self._verification_url = verification_url
        self._use_tls = use_tls

    async def send_verification_email(
        self,
        recipient: str,
        raw_token: str,
    ) -> None:
        if not self._host or not self._sender or not self._verification_url:
            raise VerificationDeliveryError(
                "Verification email delivery is not configured"
            )
        await asyncio.to_thread(self._send, recipient, raw_token)

    def _send(self, recipient: str, raw_token: str) -> None:
        separator = "&" if "?" in self._verification_url else "?"
        verification_link = (
            f"{self._verification_url}{separator}{urlencode({'token': raw_token})}"
        )
        message = EmailMessage()
        message["Subject"] = "Verify your email address"
        message["From"] = self._sender
        message["To"] = recipient
        message.set_content(
            "Complete your registration by opening this link:\n\n"
            f"{verification_link}\n"
        )

        try:
            with smtplib.SMTP(self._host, self._port, timeout=15) as client:
                if self._use_tls:
                    client.starttls()
                if self._username and self._password:
                    client.login(self._username, self._password)
                client.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise VerificationDeliveryError(
                "Unable to deliver verification email"
            ) from exc
