from __future__ import annotations


class AccountLinkingPolicy:
    """
    Quyet dinh co duoc auto-link 1 identity SSO vao 1 user local co san hay
    khong. CHI auto-link khi email da verified o CA HAI phia - neu khong se
    dinh lo hong account takeover (ke tan cong tao SSO account voi email
    nan nhan chua verify).
    """

    def can_auto_link(
        self,
        existing_user_email_verified: bool,
        incoming_identity_email_verified: bool,
    ) -> bool:

        return (
            existing_user_email_verified
            and incoming_identity_email_verified
        )