from __future__ import annotations

MFA_REQUIRED_PERMISSION_CODE = "security:mfa_required"


class MfaPolicy:
    """
    MFA bat buoc theo role duoc quyet dinh boi 1 marker permission (khong
    can cot/bang rieng) - role nao duoc gan permission nay thi moi user
    thuoc role do bi bat buoc MFA. Danh sach permission cua user duoc
    application layer truyen vao tu authz module (qua facade).
    """

    def is_mfa_required(
        self,
        user_permission_codes: set[str],
    ) -> bool:

        return MFA_REQUIRED_PERMISSION_CODE in user_permission_codes