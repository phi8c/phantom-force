from module.auth.domain.enums.auth_provider import AuthProvider


_TO_DATABASE = {
    AuthProvider.LOCAL: "LOCAL",
    AuthProvider.ENTRA: "MICROSOFT_ENTRA",
}
_TO_DOMAIN = {value: key for key, value in _TO_DATABASE.items()}


def auth_method_to_database(auth_method: AuthProvider) -> str:
    try:
        return _TO_DATABASE[auth_method]
    except KeyError as exc:
        raise ValueError(f"Unsupported policy authentication method: {auth_method}") from exc


def auth_method_to_domain(auth_method: str) -> AuthProvider:
    try:
        return _TO_DOMAIN[auth_method]
    except KeyError as exc:
        raise ValueError(f"Unknown policy authentication method: {auth_method}") from exc
