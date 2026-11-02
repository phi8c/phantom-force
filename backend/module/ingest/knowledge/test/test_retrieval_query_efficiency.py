import asyncio
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql

from module.ingest.knowledge.infrastructure.persistence.queries.retrieval_projection import ReachableStructureQuery
from module.ingest.knowledge.infrastructure.persistence.queries.discovery_cache import vector_candidate_scope
from module.ingest.knowledge.infrastructure.persistence.repositories.knowledge_repository_impl import KnowledgeRepositoryImpl
from module.ingest.knowledge.infrastructure.persistence.models import (
    KnowledgeObjectModel, KnowledgeInformationTypeModel, KnowledgeTopicModel,
)
from module.ingest.knowledge.domain.entities import (
    KnowledgeDiscoveredRequestRecord, KnowledgeMatchedEntryPointsRecord,
    KnowledgeCodeStructureRecord,
)


class RecordingSession:
    def __init__(self, models=(), rows=()):
        self.statements = []
        self.models = models
        self.rows = rows

    async def execute(self, statement):
        self.statements.append(statement)
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: self.models), all=lambda: self.rows)


def selected_sql(statement):
    return str(statement.compile(dialect=postgresql.dialect())).split('FROM', 1)[0]


class ProjectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_legacy_search_has_no_diagnostic_count_queries(self):
        statements = []
        model = SimpleNamespace(id=uuid4(), object_code='device', identifier_code='a')
        class Session:
            async def execute(self, statement):
                statements.append(statement)
                return SimpleNamespace(scalar_one_or_none=lambda: model, all=lambda: [])
        result = await KnowledgeRepositoryImpl(Session()).search_information(
            knowledge_space_id=uuid4(), object_code='device', identifier_code='a',
            information_type_code='specification', topic_codes=['maintenance'])
        self.assertEqual(result, [])
        self.assertEqual(len(statements), 2)
        self.assertTrue(all('count(' not in str(statement.compile(dialect=postgresql.dialect())).lower()
                            for statement in statements))

    async def test_vector_candidates_return_only_structure_and_keep_top_k(self):
        session = RecordingSession()
        repository = KnowledgeRepositoryImpl(session)
        await repository._vector_code_candidates(model_class=KnowledgeTopicModel,
            record_factory=repository._topic_record, knowledge_space_id=uuid4(), vector=[1.0, 0.0], seen=set())
        statement = session.statements[0]
        sql = selected_sql(statement)
        self.assertNotIn('.embedding', sql)
        self.assertNotIn('.metadata', sql)
        self.assertIn('.description', sql)
        self.assertEqual(statement._limit_clause.value, 5)
        self.assertIn('<=>', str(statement.compile(dialect=postgresql.dialect())))

    async def test_object_vector_projection_omits_both_embedding_payloads(self):
        session = RecordingSession()
        repository = KnowledgeRepositoryImpl(session)
        await repository._vector_object_candidates(knowledge_space_id=uuid4(), vector=[1.0, 0.0],
            column=KnowledgeObjectModel.object_embedding, seen=set())
        sql = selected_sql(session.statements[0])
        self.assertNotIn('.object_embedding', sql)
        self.assertNotIn('.identifier_embedding', sql)
        self.assertIn('.identifier_name', sql)

    async def test_reachable_query_returns_field_names_instead_of_data_values(self):
        session = RecordingSession()
        repository = KnowledgeRepositoryImpl(session)
        await repository._load_reachable_structure_rows(knowledge_space_id=uuid4(),
            base_filters=[KnowledgeTopicModel.code == 'topic'])
        statement = session.statements[0]
        sql = str(statement.compile(dialect=postgresql.dialect()))
        self.assertEqual([c.key for c in statement.selected_columns],
                         ['information_type_id', 'object_refs', 'topic_refs', 'field_codes'])
        self.assertIn('jsonb_object_keys', sql)
        self.assertIn('jsonb_build_object()', sql)
        self.assertIn('CASE WHEN', sql)
        self.assertIn('SELECT DISTINCT', sql)

    async def test_final_retrieval_keeps_full_answer_data_but_not_raw_model_output(self):
        identity = uuid4()
        model = SimpleNamespace(id=identity, summary='Original', data={'table': {'rows': [[1, 2]]}},
            object_refs=[{'object_id': 'source'}], topic_refs=[], source_refs=[{'chunk_id': 'chunk'}], confidence=.9)
        session = RecordingSession(rows=[(model, 'type')])
        repository = KnowledgeRepositoryImpl(session)
        discovered = KnowledgeDiscoveredRequestRecord('request', KnowledgeMatchedEntryPointsRecord(
            objects=[], information_types=[KnowledgeCodeStructureRecord('type', None, None)], topics=[]))
        result = await repository.retrieve_for_selection(knowledge_space_id=uuid4(), discovered_request=discovered,
            information_type_codes=['type'], topic_codes=[], field_codes=['table'])
        self.assertEqual(result[0].information_id, identity)
        self.assertEqual(result[0].data, model.data)
        self.assertEqual(result[0].source_refs, model.source_refs)
        sql = selected_sql(session.statements[0])
        self.assertNotIn('.raw_model_output', sql)
        self.assertNotIn('.embedding', sql)
        self.assertNotIn('.metadata', sql)

    async def test_information_type_entry_points_share_one_in_subquery(self):
        filters = KnowledgeRepositoryImpl._entry_point_filters_from_matches(knowledge_space_id=uuid4(),
            matched_entry_points=KnowledgeMatchedEntryPointsRecord(objects=[], topics=[],
                information_types=[KnowledgeCodeStructureRecord(code, None, None) for code in ('a', 'b', 'a')]))
        self.assertEqual(len(filters), 1)
        sql = str(filters[0].compile(dialect=postgresql.dialect()))
        self.assertEqual(sql.count('SELECT'), 1)


class ReachableRegistryTests(unittest.IsolatedAsyncioTestCase):
    async def test_four_registries_use_one_statement_and_preserve_space_and_unknown_fields(self):
        engine = create_engine('sqlite://')
        try:
            with engine.connect() as connection:
                connection.exec_driver_sql('''CREATE TABLE knowledge_objects (id TEXT, knowledge_space_id TEXT,
                    object_code TEXT, identifier_code TEXT, object_name TEXT, identifier_name TEXT, description TEXT)''')
                for table in ('knowledge_information_types', 'knowledge_topics', 'knowledge_information_fields'):
                    connection.exec_driver_sql(f'''CREATE TABLE {table} (id TEXT, knowledge_space_id TEXT,
                        code TEXT, name TEXT, description TEXT, data_type TEXT)''')
                space, other, obj, type_id = uuid4(), uuid4(), uuid4(), uuid4()
                connection.exec_driver_sql('INSERT INTO knowledge_objects VALUES (?,?,?,?,?,?,?)',
                    (obj.hex, space.hex, 'device', 'device_a', 'Device', 'A', 'Original object'))
                connection.exec_driver_sql('INSERT INTO knowledge_information_types VALUES (?,?,?,?,?,?)',
                    (type_id.hex, space.hex, 'specification', 'Specification', None, None))
                for selected_space, name in ((space, 'Topic'), (other, 'Foreign topic')):
                    connection.exec_driver_sql('INSERT INTO knowledge_topics VALUES (?,?,?,?,?,?)',
                        (uuid4().hex, selected_space.hex, 'topic', name, None, None))
                connection.exec_driver_sql('INSERT INTO knowledge_information_fields VALUES (?,?,?,?,?,?)',
                    (uuid4().hex, space.hex, 'voltage', 'Voltage', None, 'number'))
                calls = []
                class Adapter:
                    async def execute(self, statement):
                        calls.append(statement)
                        return connection.execute(statement)
                result = await ReachableStructureQuery(Adapter()).load(knowledge_space_id=space,
                    object_ids={obj}, type_ids={type_id}, topic_codes={'topic'}, field_codes={'voltage', 'missing'})
                self.assertEqual(len(calls), 1)
                self.assertEqual(result.objects[0].identifier_code, 'device_a')
                self.assertEqual(result.information_types[0].code, 'specification')
                self.assertEqual([topic.name for topic in result.topics], ['Topic'])
                self.assertEqual([field.code for field in result.fields], ['missing', 'voltage'])
                self.assertIsNone(result.fields[0].name)
                self.assertEqual(result.fields[1].data_type, 'number')
        finally:
            engine.dispose()

    async def test_empty_structure_needs_no_query(self):
        result = await ReachableStructureQuery(None).load(knowledge_space_id=uuid4(),
            object_ids=set(), type_ids=set(), topic_codes=set(), field_codes=set())
        self.assertEqual(result.objects + result.fields + result.topics + result.information_types, [])

    async def test_compact_and_legacy_rows_have_equivalent_field_sets(self):
        compact = [SimpleNamespace(_mapping={'field_codes': ['a', 'b']}), SimpleNamespace(_mapping={'field_codes': None})]
        legacy = [SimpleNamespace(_mapping={'data': {'a': 'Huge value', 'b': 123}}), SimpleNamespace(_mapping={'data': None})]
        self.assertEqual(KnowledgeRepositoryImpl._field_codes_from_rows(compact),
                         KnowledgeRepositoryImpl._field_codes_from_rows(legacy))


class VectorCacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_discovery_cache_scopes_do_not_share_values(self):
        from module.ingest.knowledge.infrastructure.persistence.queries.discovery_cache import vector_candidates
        calls = []
        async def worker(value):
            async def load():
                calls.append(value)
                await asyncio.sleep(0)
                return [value]
            with vector_candidate_scope():
                first = await vector_candidates(('same-key',), load)
                second = await vector_candidates(('same-key',), load)
                self.assertEqual(first, (value,))
                self.assertEqual(second, first)
        await asyncio.gather(worker('a'), worker('b'))
        self.assertCountEqual(calls, ['a', 'b'])

    async def test_vector_cache_distinguishes_object_and_identifier_columns(self):
        model = SimpleNamespace(object_code='device', identifier_code='a', object_name='Device',
                                identifier_name='A', description=None)
        session = RecordingSession(models=[model])
        repository = KnowledgeRepositoryImpl(session)
        space = uuid4()
        with vector_candidate_scope():
            for column in (KnowledgeObjectModel.object_embedding, KnowledgeObjectModel.identifier_embedding):
                await repository._vector_object_candidates(knowledge_space_id=space, column=column,
                    vector=[1., 0.], seen=set())
        self.assertEqual(len(session.statements), 2)

    async def test_repeated_vector_read_is_cached_before_seen_filtering_and_expires(self):
        session = RecordingSession(models=[SimpleNamespace(code=code, name=code, description=None) for code in ('a', 'b')])
        repository = KnowledgeRepositoryImpl(session)
        space = uuid4()
        async def read(seen, selected_space=space):
            return await repository._vector_code_candidates(model_class=KnowledgeTopicModel,
                record_factory=repository._topic_record, knowledge_space_id=selected_space,
                vector=[1.0, 0.0], seen=seen)
        with vector_candidate_scope():
            first = await read({'a'})
            second = await read({'b'})
            self.assertEqual([value.code for value in first], ['b'])
            self.assertEqual([value.code for value in second], ['a'])
            self.assertEqual(len(session.statements), 1)
            await read(set(), uuid4())
            self.assertEqual(len(session.statements), 2)
        with vector_candidate_scope():
            await read(set())
        self.assertEqual(len(session.statements), 3)

    async def test_discover_scopes_cache_across_requests_but_not_across_calls(self):
        class Repository(KnowledgeRepositoryImpl):
            async def _discover_request(self, *, knowledge_space_id, request, request_vectors=None):
                await self._vector_code_candidates(model_class=KnowledgeTopicModel,
                    record_factory=self._topic_record, knowledge_space_id=knowledge_space_id,
                    vector=[1., 0.], seen=set())
                return None
        session = RecordingSession()
        repository = Repository(session)
        space = uuid4()
        await repository.discover(knowledge_space_id=space, requests=[{'request_id': 'a'}, {'request_id': 'b'}])
        self.assertEqual(len(session.statements), 1)
        await repository.discover(knowledge_space_id=space, requests=[{'request_id': 'a'}])
        self.assertEqual(len(session.statements), 2)


class DiagnosticTests(unittest.TestCase):
    def test_disabled_trace_does_not_serialize_or_write(self):
        from shared.logging.chat_diagnostics import print_chat_trace
        class Expensive:
            def __str__(self):
                raise AssertionError('Trace must return before rendering')
        with patch.dict('os.environ', {'CHAT_TRACE_ENABLED': '0'}):
            print_chat_trace('TEST', Expensive())

    def test_explicit_trace_can_still_write_debug_payload(self):
        from shared.logging import chat_diagnostics
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trace.log'
            with patch.dict('os.environ', {'CHAT_TRACE_ENABLED': '1'}), patch.object(chat_diagnostics, '_TRACE_PATH', path), patch('sys.stdout', io.StringIO()):
                chat_diagnostics.print_chat_trace('TEST', {'value': 'payload'})
            self.assertIn('payload', path.read_text(encoding='utf8'))
