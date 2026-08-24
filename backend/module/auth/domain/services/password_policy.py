from __future__ import annotations

MIN_PASSWORD_LENGTH = 12
PASSWORD_HISTORY_LIMIT = 5


class PasswordPolicy:
    """
    Theo NIST SP 800-63B: uu tien do dai hon complexity rules cung nhac,
    khong bat doi mat khau dinh ky. Viec check trung password_history
    (can PasswordHasher.verify) thuc hien o use case, khong o day - class
    nay chi chua rule khong can goi ra ngoai.
    """

    def is_valid_length(
        self,
        plain_password: str,
    ) -> bool:

        return len(plain_password) >= MIN_PASSWORD_LENGTH

    def history_limit(
        self,
    ) -> int:

        return PASSWORD_HISTORY_LIMIT