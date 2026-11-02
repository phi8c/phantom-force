import asyncio
import json
import math
from pathlib import Path
import tempfile

from module.structured_data.domain.contracts import ArtifactStore, Catalog, QueryPlanner, StructuredQueryEngine, WorkbookBuilder
from .query_compiler import QueryCompiler, QueryRejected


async def blocking(operation, *args, **kwargs):
    task = asyncio.create_task(asyncio.to_thread(operation, *args, **kwargs))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        await asyncio.gather(task, return_exceptions=True)
        raise


def dataset_text(dataset):
    return json.dumps(dataset.descriptor(),ensure_ascii=False,default=str)


def embedding_parts(dataset):
    context = json.dumps({'name':dataset.name[:160],'file':dataset.file_name[:160],'sheet':dataset.sheet,
                          'description':(dataset.description or '')[:250]},ensure_ascii=False)
    parts, current = [], context
    for column in dataset.columns:
        line = json.dumps({'column':column.name,'type':column.data_type,
                           'description':column.description},ensure_ascii=False)
        if len((current+'\n'+line).encode('utf8')) > 6000:
            parts.append(current)
            current = context
        current += '\n'+line
    parts.append(current)
    return parts


class StructuredBuildService:
    def __init__(self, *, builder: WorkbookBuilder, catalog: Catalog, artifacts: ArtifactStore,
                 config_service, embedder_factory):
        self.builder, self.catalog, self.artifacts = builder, catalog, artifacts
        self.config = config_service
        self.embedder_factory = embedder_factory

    async def build(self, *, source, file_name, document_id, ingestion_job_id):
        await self.catalog.ensure_ready()
        pair = await self.config.get_config(ingestion_job_id)
        if pair is None:
            raise ValueError('Ingestion job/configuration not found for XLSX')
        job, config = pair
        settings = (config.configuration or {}).get('structured_data', {})
        with tempfile.TemporaryDirectory(prefix='xlsx-build-') as directory:
            built = await blocking(self.builder.build, source, Path(directory),
                space=job.knowledge_space_id, document=document_id, file_name=file_name, configuration=settings)
            for value in built:
                await self.artifacts.upload(value.dataset.parquet_path, value.parquet, 'application/vnd.apache.parquet')
                if value.formulas:
                    await self.artifacts.upload(value.dataset.formulas_path, value.formulas, 'application/x-ndjson')
            embedder = await self.embedder_factory(job.knowledge_space_id)
            pieces = [(index,text) for index,value in enumerate(built) for text in embedding_parts(value.dataset)]
            sums = [None] * len(built)
            dimension = None
            for start in range(0,len(pieces),16):
                batch = pieces[start:start+16]
                embedded = await embedder.embed_texts([text for _,text in batch])
                if len(embedded) != len(batch):
                    raise ValueError('Dataset embedding provider returned incomplete results')
                for (index,_),vector in zip(batch,embedded):
                    if not vector or any(type(x) not in (int,float) or not math.isfinite(x) for x in vector):
                        raise ValueError('Dataset embedding provider returned invalid values')
                    norm = math.sqrt(sum(x*x for x in vector))
                    if not norm:
                        raise ValueError('Dataset embedding vector must not be zero')
                    dimension = dimension or len(vector)
                    if len(vector) != dimension:
                        raise ValueError('Dataset embedding dimensions changed within a build')
                    if sums[index] is None:
                        sums[index] = [0.] * len(vector)
                    if len(sums[index]) != len(vector):
                        raise ValueError('Dataset embedding dimensions changed within a build')
                    sums[index] = [a+b/norm for a,b in zip(sums[index],vector)]
            vectors = []
            for values in sums:
                norm = math.sqrt(sum(x*x for x in values))
                if not norm:
                    raise ValueError('Dataset metadata embeddings cancelled to a zero vector')
                vectors.append([x/norm for x in values])
            datasets = [value.dataset for value in built]
            await self.catalog.publish(job.knowledge_space_id, document_id, datasets, vectors,
                                       job_id=ingestion_job_id, run_created_at=job.created_at)
            # Persist an inspectable catalog extraction asset. The extraction
            # router completes this branch without scheduling text chunking or
            # classification; spreadsheet records remain only in Parquet.
            return {'schema_version':2,'document_id':str(document_id),'title':file_name,
                'extraction':{'engine':'xlsx-structured','engine_version':'1','structure_quality':'flat',
                    'warnings':list(dict.fromkeys(w for d in datasets for w in d.warnings))},
                'blocks':[{'id':str(d.id),'order':i,'kind':'paragraph','source':{'part_id':str(d.id)},
                    'text':'DATASET CATALOG ONLY. Statistics describe the dataset; query its Parquet records for business answers.\n'+dataset_text(d),
                    'table_id':None,'section_id':None} for i,d in enumerate(datasets)],'tables':[],'sections':[],
                'structured_dataset_ids':[str(d.id) for d in datasets]}


class StructuredQueryService:
    def __init__(self, *, catalog: Catalog, artifacts: ArtifactStore, planner: QueryPlanner,
                 engine: StructuredQueryEngine, embedder_factory):
        self.catalog, self.artifacts, self.planner, self.engine = catalog, artifacts, planner, engine
        self.embedder_factory = embedder_factory

    async def query(self, *, knowledge_space_id, question):
        if not await self.catalog.has_datasets(knowledge_space_id):
            return None
        embedder = await self.embedder_factory(knowledge_space_id)
        vectors = await embedder.embed_texts([question])
        if len(vectors) != 1 or not vectors[0] or any(type(x) not in (int,float) or not math.isfinite(x) for x in vectors[0]) or not any(x != 0 for x in vectors[0]):
            raise ValueError('Question embedding is missing')
        candidates = await self.catalog.search(knowledge_space_id, vectors[0])
        if not candidates:
            return None
        feedback = None
        for attempt in range(2):
            try:
                plan = await self.planner.plan(question,candidates,feedback=feedback)
                if plan is None:
                    if feedback:
                        raise QueryRejected(feedback)
                    return None
                compiled = QueryCompiler().compile(plan,candidates)
                if any(d.knowledge_space_id != knowledge_space_id for d in compiled.datasets):
                    raise QueryRejected('Dataset scope does not match the authorized knowledge space')
                with tempfile.TemporaryDirectory(prefix='xlsx-query-') as directory:
                    paths = {}
                    for dataset in compiled.datasets:
                        target = Path(directory) / f'{dataset.id}.parquet'
                        await self.artifacts.download(dataset.parquet_path,target,dataset.parquet_sha256)
                        paths[dataset.id] = target
                    return await blocking(self.engine.execute,plan,candidates,paths)
            except QueryRejected as error:
                feedback = str(error)
                if attempt:
                    raise
        raise QueryRejected('Structured planning failed')
