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
from module.auth.infrastructure.persistence.models.auth_session_model import (
    AuthSessionModel,
)
from module.auth.infrastructure.persistence.models.credential_model import CredentialModel
from module.auth.infrastructure.persistence.models.knowledge_space_auth_policy_model import (
    KnowledgeSpaceAuthPolicyModel,
)
from module.auth.infrastructure.persistence.models.management_auth_policy_model import (
    ManagementAuthPolicyModel,
)


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_auth_models_match_required_database_tables_and_columns() -> None:
    expected = {
        AuthSessionModel: {
            "id", "user_id", "session_token_hash", "auth_method", "ip_address",
            "user_agent", "device_fingerprint", "issued_at", "last_seen_at",
            "idle_expires_at", "absolute_expires_at", "revoked_at",
            "revoked_reason", "context_type", "knowledge_space_id",
            "identity_link_id", "authenticated_at", "mfa_verified_at",
        },
        KnowledgeSpaceAuthPolicyModel: {
            "id", "knowledge_space_id", "auth_method", "tenant_id", "require_mfa",
            "idle_timeout_minutes", "absolute_timeout_minutes", "is_active",
            "created_by", "created_at", "updated_at",
        },
        ManagementAuthPolicyModel: {
            "id", "auth_method", "tenant_id", "require_mfa",
            "idle_timeout_minutes", "absolute_timeout_minutes",
            "reauthentication_minutes", "is_active", "created_at", "updated_at",
        },
        CredentialModel: {
            "user_id", "password_hash", "password_algo", "password_changed_at",
            "failed_attempts", "locked_until", "mfa_enabled",
            "mfa_secret_encrypted", "created_at", "updated_at",
        },
    }
    expected_tables = {
        AuthSessionModel: "auth_sessions",
        KnowledgeSpaceAuthPolicyModel: "knowledge_space_auth_policies",
        ManagementAuthPolicyModel: "management_auth_policy",
        CredentialModel: "credentials",
    }

    for model, expected_columns in expected.items():
        assert model.__table__.schema == "iam"
        assert model.__table__.name == expected_tables[model]
        assert set(model.__table__.columns.keys()) == expected_columns


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
