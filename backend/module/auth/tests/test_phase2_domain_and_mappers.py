from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from module.auth.domain.entities.auth_session import AuthSession
from module.auth.domain.entities.knowledge_space_auth_policy import (
    KnowledgeSpaceAuthPolicy,
)
from module.auth.domain.entities.management_auth_policy import ManagementAuthPolicy
from module.auth.domain.enums.auth_provider import AuthProvider
from module.auth.domain.enums.authentication_context_type import (
    AuthenticationContextType,
)
from module.auth.infrastructure.persistence.mappers.auth_session_mapper import (
    AuthSessionMapper,
)
from module.auth.infrastructure.persistence.mappers.knowledge_space_auth_policy_mapper import (
    KnowledgeSpaceAuthPolicyMapper,
)
from module.auth.infrastructure.persistence.mappers.management_auth_policy_mapper import (
    ManagementAuthPolicyMapper,
)


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_auth_session_mapper_round_trips_new_fields() -> None:
    knowledge_space_id = uuid4()
    identity_link_id = uuid4()
    session = AuthSession.create(
        id=uuid4(),
        user_id=uuid4(),
        session_token_hash="hash",
        auth_method=AuthProvider.ENTRA,
        ip_address="127.0.0.1",
        user_agent="test",
        device_fingerprint="device",
        now=NOW,
        idle_expires_at=NOW + timedelta(minutes=30),
        absolute_expires_at=NOW + timedelta(hours=8),
        context_type=AuthenticationContextType.KNOWLEDGE_SPACE,
        knowledge_space_id=knowledge_space_id,
        identity_link_id=identity_link_id,
        mfa_verified_at=NOW,
    )

    mapped = AuthSessionMapper.to_domain(AuthSessionMapper.to_model(session))

    assert mapped == session


def test_auth_session_rejects_invalid_context_scope() -> None:
    with pytest.raises(ValueError):
        AuthSession.create(
            id=uuid4(),
            user_id=uuid4(),
            session_token_hash="hash",
            auth_method=AuthProvider.LOCAL,
            ip_address=None,
            user_agent=None,
            device_fingerprint=None,
            now=NOW,
            idle_expires_at=NOW + timedelta(minutes=15),
            absolute_expires_at=NOW + timedelta(hours=8),
            context_type=AuthenticationContextType.KNOWLEDGE_SPACE,
        )


def test_knowledge_space_policy_mapper_maps_database_auth_method() -> None:
    policy = KnowledgeSpaceAuthPolicy(
        id=uuid4(),
        knowledge_space_id=uuid4(),
        auth_method=AuthProvider.ENTRA,
        tenant_id="tenant-id",
        require_mfa=True,
        idle_timeout_minutes=30,
        absolute_timeout_minutes=480,
        is_active=True,
        created_by=uuid4(),
        created_at=NOW,
        updated_at=NOW,
    )

    model = KnowledgeSpaceAuthPolicyMapper.to_model(policy)

    assert model.auth_method == "MICROSOFT_ENTRA"
    assert KnowledgeSpaceAuthPolicyMapper.to_domain(model) == policy


def test_management_policy_mapper_round_trip() -> None:
    policy = ManagementAuthPolicy(
        id=uuid4(),
        auth_method=AuthProvider.LOCAL,
        tenant_id=None,
        require_mfa=True,
        idle_timeout_minutes=15,
        absolute_timeout_minutes=480,
        reauthentication_minutes=15,
        is_active=True,
        created_at=NOW,
        updated_at=NOW,
    )

    mapped = ManagementAuthPolicyMapper.to_domain(
        ManagementAuthPolicyMapper.to_model(policy)
    )

    assert mapped == policy


def test_policy_rejects_provider_not_supported_by_database() -> None:
    with pytest.raises(ValueError):
        KnowledgeSpaceAuthPolicy(
            id=uuid4(),
            knowledge_space_id=uuid4(),
            auth_method=AuthProvider.GOOGLE,
            tenant_id=None,
            require_mfa=False,
            idle_timeout_minutes=30,
            absolute_timeout_minutes=480,
            is_active=True,
            created_by=None,
            created_at=NOW,
            updated_at=NOW,
        )
