from app.domain.entities.identity_link import (
    IdentityLink,
)

from app.domain.enums.auth_provider import (
    AuthProvider,
)

from app.infrastructure.persistence.models.identity_link_model import (
    IdentityLinkModel,
)


class IdentityLinkMapper:

    @staticmethod
    def to_domain(
        model: IdentityLinkModel,
    ) -> IdentityLink:

        return IdentityLink(
            id=model.id,
            user_id=model.user_id,
            provider=AuthProvider(model.provider),
            external_sub=model.external_sub,
            tenant_id=model.tenant_id,
            email_at_link=model.email_at_link,
            linked_at=model.linked_at,
        )

    @staticmethod
    def to_model(
        entity: IdentityLink,
    ) -> IdentityLinkModel:

        return IdentityLinkModel(
            id=entity.id,
            user_id=entity.user_id,
            provider=entity.provider.value,
            external_sub=entity.external_sub,
            tenant_id=entity.tenant_id,
            email_at_link=entity.email_at_link,
            linked_at=entity.linked_at,
        )