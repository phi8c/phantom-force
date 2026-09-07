from module.ingest.knowledge.domain.entities import (
    KnowledgeDocumentType,
    KnowledgeInformation,
    KnowledgeInformationField,
    KnowledgeInformationType,
    KnowledgeObject,
    KnowledgeTopic,
)
from module.ingest.knowledge.infrastructure.persistence.models import (
    KnowledgeDocumentTypeModel,
    KnowledgeInformationFieldModel,
    KnowledgeInformationModel,
    KnowledgeInformationTypeModel,
    KnowledgeObjectModel,
    KnowledgeTopicModel,
)


class KnowledgeMapper:

    @staticmethod
    def document_type_to_entity(
        model: KnowledgeDocumentTypeModel,
    ) -> KnowledgeDocumentType:
        return KnowledgeDocumentType(
            id=model.id,
            knowledge_space_id=model.knowledge_space_id,
            code=model.code,
            name=model.name,
            description=model.description,
            structuring_guidance=model.structuring_guidance,
            metadata=model.metadata_payload,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def object_to_entity(
        model: KnowledgeObjectModel,
    ) -> KnowledgeObject:
        return KnowledgeObject(
            id=model.id,
            knowledge_space_id=model.knowledge_space_id,
            object_code=model.object_code,
            identifier_code=model.identifier_code,
            object_name=model.object_name,
            identifier_name=model.identifier_name,
            description=model.description,
            aliases=model.aliases,
            metadata=model.metadata_payload,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def information_type_to_entity(
        model: KnowledgeInformationTypeModel,
    ) -> KnowledgeInformationType:
        return KnowledgeInformationType(
            id=model.id,
            knowledge_space_id=model.knowledge_space_id,
            code=model.code,
            name=model.name,
            description=model.description,
            metadata=model.metadata_payload,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def information_field_to_entity(
        model: KnowledgeInformationFieldModel,
    ) -> KnowledgeInformationField:
        return KnowledgeInformationField(
            id=model.id,
            knowledge_space_id=model.knowledge_space_id,
            code=model.code,
            name=model.name,
            description=model.description,
            data_type=model.data_type,
            unit_type=model.unit_type,
            metadata=model.metadata_payload,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def topic_to_entity(
        model: KnowledgeTopicModel,
    ) -> KnowledgeTopic:
        return KnowledgeTopic(
            id=model.id,
            knowledge_space_id=model.knowledge_space_id,
            code=model.code,
            name=model.name,
            description=model.description,
            metadata=model.metadata_payload,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def information_to_entity(
        model: KnowledgeInformationModel,
    ) -> KnowledgeInformation:
        return KnowledgeInformation(
            id=model.id,
            knowledge_space_id=model.knowledge_space_id,
            information_type_id=model.information_type_id,
            summary=model.summary,
            data=model.data,
            object_refs=model.object_refs,
            topic_refs=model.topic_refs,
            source_refs=model.source_refs,
            confidence=model.confidence,
            raw_model_output=model.raw_model_output,
            metadata=model.metadata_payload,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
