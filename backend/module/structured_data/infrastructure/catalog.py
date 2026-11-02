from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Integer, String, Text, case, func, select, text, update
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID, insert
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import Base
from module.structured_data.domain.models import Column, Dataset


class StructuredDatasetModel(Base):
    __tablename__ = 'structured_datasets'
    __table_args__ = {'schema':'public'}
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    knowledge_space_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    ingestion_job_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    embedding = mapped_column(Vector(), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    run_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def encode_dataset(dataset):
    return {**asdict(dataset), 'id':str(dataset.id), 'document_id':str(dataset.document_id),
            'knowledge_space_id':str(dataset.knowledge_space_id)}


def decode_dataset(payload):
    value = dict(payload)
    for key in ('id','document_id','knowledge_space_id'):
        value[key] = UUID(value[key])
    value['columns'] = tuple(Column(**item) for item in value['columns'])
    value['warnings'] = tuple(value.get('warnings', []))
    value['relationships'] = tuple(value.get('relationships', []))
    return Dataset(**value)


class SqlDatasetCatalog:
    def __init__(self, session):
        self.session = session

    async def _ready(self):
        # Keep pre-migration text-only deployments operational. XLSX writes fail
        # explicitly below rather than being silently routed to a text extractor.
        return (await self.session.execute(text("SELECT to_regclass('public.structured_datasets') IS NOT NULL"))).scalar_one()

    async def has_datasets(self, space):
        if not await self._ready():
            return False
        return (await self.session.execute(select(StructuredDatasetModel.id).where(
            StructuredDatasetModel.knowledge_space_id == space, StructuredDatasetModel.active.is_(True),
        ).limit(1))).first() is not None

    async def ensure_ready(self):
        if not await self._ready():
            raise ValueError('Apply backend/scripts/create_structured_datasets.sql before ingesting XLSX')

    async def publish(self, space, document, datasets, embeddings, *, job_id, run_created_at):
        if not await self._ready():
            raise ValueError('Apply backend/scripts/create_structured_datasets.sql before ingesting XLSX')
        if not datasets or len(datasets) != len(embeddings):
            raise ValueError('Every dataset needs a catalog embedding')
        if any(d.knowledge_space_id != space or d.document_id != document for d in datasets):
            raise ValueError('Dataset publication scope mismatch')
        key = int.from_bytes(hashlib.sha256(f'{space}:{document}'.encode()).digest()[:8], 'big', signed=True)
        await self.session.execute(select(func.pg_advisory_xact_lock(key)))
        latest = (await self.session.execute(select(func.max(StructuredDatasetModel.run_created_at)).where(
            StructuredDatasetModel.knowledge_space_id == space, StructuredDatasetModel.document_id == document,
        ))).scalar_one()
        if latest is not None and latest > run_created_at:
            return  # A slower older run must not replace the latest published snapshot.
        await self.session.execute(update(StructuredDatasetModel).where(
            StructuredDatasetModel.knowledge_space_id == space, StructuredDatasetModel.document_id == document,
        ).values(active=False))
        rows = [dict(id=d.id, knowledge_space_id=space, document_id=document, ingestion_job_id=job_id,
            version=d.version, name=d.name, payload=encode_dataset(d), embedding=vector,
            active=True, run_created_at=run_created_at) for d,vector in zip(datasets,embeddings)]
        statement = insert(StructuredDatasetModel).values(rows)
        await self.session.execute(statement.on_conflict_do_update(index_elements=['id'], set_={
            key:getattr(statement.excluded,key) for key in ('payload','embedding','active','run_created_at','ingestion_job_id','name')}))
        # Transaction belongs to the extraction unit of work. Never commit here.

    async def search(self, space, vector, limit=4):
        if not 1 <= limit <= 8:
            raise ValueError('Catalog retrieval limit must be from 1 to 8')
        distance = case((func.vector_dims(StructuredDatasetModel.embedding) == len(vector),
                        StructuredDatasetModel.embedding.cosine_distance(vector)), else_=None)
        rows = (await self.session.execute(select(StructuredDatasetModel.payload).where(
            StructuredDatasetModel.knowledge_space_id == space, StructuredDatasetModel.active.is_(True),
        ).order_by(distance.asc().nulls_last(), StructuredDatasetModel.id).limit(limit))).scalars().all()
        matched = [decode_dataset(value) for value in rows]
        if not matched:
            return []
        first = matched[0]
        related = (await self.session.execute(select(StructuredDatasetModel.payload).where(
            StructuredDatasetModel.knowledge_space_id == space,
            StructuredDatasetModel.document_id == first.document_id,
            StructuredDatasetModel.version == first.version,
            StructuredDatasetModel.active.is_(True),
        ).order_by(StructuredDatasetModel.id).limit(33))).scalars().all()
        if len(related) > 32:
            raise ValueError('Workbook has more than 32 active datasets; narrow the catalog selection before querying')
        by_id = {d.id:d for d in matched}
        for value in related:
            dataset = decode_dataset(value)
            by_id.setdefault(dataset.id,dataset)
        return list(by_id.values())
