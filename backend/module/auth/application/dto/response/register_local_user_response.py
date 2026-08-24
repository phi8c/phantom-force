from dataclasses import dataclass

@dataclass
class RegisterLocalUserResult:
    """
    1 object duy nhat, ten field ro nghia - thay the cho tuple mo ho.
    raw_verification_token = None khi email da ton tai tu truoc (khong tao
    gi ca, chi tra ket qua giong het truong hop thanh cong).
    """

    message: str

    raw_verification_token: str | None