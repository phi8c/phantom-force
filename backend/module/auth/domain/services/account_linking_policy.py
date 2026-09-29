from __future__ import annotations


class AccountLinkingPolicy:
    """Email equality is never sufficient proof for identity linking."""

    def can_auto_link(
        self,
        existing_user_email_verified: bool,
        incoming_identity_email_verified: bool,
    ) -> bool:

        return False
