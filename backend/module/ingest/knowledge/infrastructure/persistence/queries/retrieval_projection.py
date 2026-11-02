"""Small read projections for discovery; no embedding/model-output hydration."""
from sqlalchemy import literal, select, union_all
from sqlalchemy.orm import load_only

from module.ingest.knowledge.domain.entities import (
    KnowledgeCodeStructureRecord, KnowledgeMatchedEntryPointsRecord, KnowledgeObjectStructureRecord,
)
from module.ingest.knowledge.infrastructure.persistence.models import (
    KnowledgeObjectModel, KnowledgeInformationTypeModel, KnowledgeTopicModel,
    KnowledgeInformationFieldModel, KnowledgeInformationModel,
)


def structure_options(model):
    if model is KnowledgeObjectModel:
        columns = [model.object_code, model.identifier_code, model.object_name,
                   model.identifier_name, model.description]
    else:
        columns = [model.code, model.name, model.description]
        if model is KnowledgeInformationFieldModel:
            columns.append(model.data_type)
    return load_only(*columns, raiseload=True)


def information_options():
    model = KnowledgeInformationModel
    return load_only(model.id, model.summary, model.data, model.object_refs, model.topic_refs,
                     model.source_refs, model.confidence, raiseload=True)


class ReachableStructureQuery:
    def __init__(self, session):
        self.session = session

    async def load(self, *, knowledge_space_id, object_ids, type_ids, topic_codes, field_codes):
        branches = []
        if object_ids:
            model = KnowledgeObjectModel
            branches.append(select(literal('objects').label('kind'), model.object_code.label('code'),
                model.identifier_code, model.object_name.label('name'), model.identifier_name,
                model.description, literal(None).label('data_type')).where(
                    model.knowledge_space_id == knowledge_space_id, model.id.in_(object_ids)))
        for kind, model, values, column in (
            ('information_types', KnowledgeInformationTypeModel, type_ids, KnowledgeInformationTypeModel.id),
            ('topics', KnowledgeTopicModel, topic_codes, KnowledgeTopicModel.code),
            ('fields', KnowledgeInformationFieldModel, field_codes, KnowledgeInformationFieldModel.code),
        ):
            if values:
                branches.append(select(literal(kind).label('kind'), model.code,
                    literal(None).label('identifier_code'), model.name,
                    literal(None).label('identifier_name'), model.description,
                    model.data_type if kind == 'fields' else literal(None).label('data_type')).where(
                        model.knowledge_space_id == knowledge_space_id, column.in_(values)))
        result = KnowledgeMatchedEntryPointsRecord(objects=[], information_types=[], topics=[], fields=[])
        fields = {}
        if branches:
            statement = union_all(*branches) if len(branches) > 1 else branches[0]
            rows = (await self.session.execute(statement)).mappings().all()
            for row in rows:
                if row['kind'] == 'objects':
                    result.objects.append(KnowledgeObjectStructureRecord(
                        row['code'], row['identifier_code'], row['name'], row['identifier_name'], row['description']))
                else:
                    record = KnowledgeCodeStructureRecord(row['code'], row['name'], row['description'], row['data_type'])
                    if row['kind'] == 'fields':
                        fields[record.code] = record
                    else:
                        getattr(result, row['kind']).append(record)
        result.fields = [fields.get(code, KnowledgeCodeStructureRecord(code, None, None)) for code in sorted(field_codes)]
        return result
