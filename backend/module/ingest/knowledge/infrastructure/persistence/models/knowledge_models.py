from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from shared.database.base import Base


class KnowledgeDocumentTypeModel(
    Base,
):
    __tablename__ = "knowledge_document_types"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_space_id",
            "code",
            name="uq_knowledge_document_types_space_code",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    knowledge_space_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_spaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(150), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    structuring_guidance: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    embedding = mapped_column(Vector(), nullable=True)
    metadata_payload: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class KnowledgeObjectModel(Base):
    __tablename__ = "knowledge_objects"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    knowledge_space_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge_spaces.id", ondelete="CASCADE"), nullable=False)
    object_code: Mapped[str] = mapped_column(String(200), nullable=False)
    identifier_code: Mapped[str | None] = mapped_column(String(300), nullable=True)
    object_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    identifier_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    aliases: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    object_embedding = mapped_column(Vector(), nullable=True)
    identifier_embedding = mapped_column(Vector(), nullable=True)
    metadata_payload: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class KnowledgeInformationTypeModel(Base):
    __tablename__ = "knowledge_information_types"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_space_id",
            "code",
            name="uq_knowledge_information_types_space_code",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    knowledge_space_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge_spaces.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding = mapped_column(Vector(), nullable=True)
    metadata_payload: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class KnowledgeInformationFieldModel(Base):
    __tablename__ = "knowledge_information_fields"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_space_id",
            "code",
            name="uq_knowledge_information_fields_space_code",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    knowledge_space_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge_spaces.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding = mapped_column(Vector(), nullable=True)
    metadata_payload: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class KnowledgeTopicModel(Base):
    __tablename__ = "knowledge_topics"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_space_id",
            "code",
            name="uq_knowledge_topics_space_code",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    knowledge_space_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge_spaces.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding = mapped_column(Vector(), nullable=True)
    metadata_payload: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class KnowledgeInformationModel(Base):
    __tablename__ = "knowledge_information"
    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_knowledge_information_confidence",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    knowledge_space_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge_spaces.id", ondelete="CASCADE"), nullable=False)
    information_type_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge_information_types.id", ondelete="SET NULL"), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    object_refs: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    topic_refs: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    source_refs: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    embedding = mapped_column(Vector(), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_model_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_payload: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
