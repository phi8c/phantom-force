from module.auth.domain.enums.auth_provider import AuthProvider


def validate_auth_policy(
    auth_method: AuthProvider,
    tenant_id: str | None,
    idle_timeout_minutes: int,
    absolute_timeout_minutes: int,
) -> None:
    if auth_method not in (AuthProvider.LOCAL, AuthProvider.ENTRA):
        raise ValueError("Unsupported authentication method")
    if auth_method is AuthProvider.LOCAL and tenant_id is not None:
        raise ValueError("Local authentication cannot have a tenant")
    if auth_method is AuthProvider.ENTRA and not tenant_id:
        raise ValueError("Microsoft Entra authentication requires a tenant")
    if idle_timeout_minutes <= 0 or absolute_timeout_minutes <= 0:
        raise ValueError("Authentication timeouts must be positive")
    if idle_timeout_minutes > absolute_timeout_minutes:
        raise ValueError("Idle timeout cannot exceed absolute timeout")
