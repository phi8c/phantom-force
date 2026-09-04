# Ingest Refactor Phase 1 Audit

## Goal

Refactor ingest architecture ownership without behavior or schema changes.
Integration code should become module-to-module adapters only. SQLAlchemy,
ORM models, repositories, and engine implementations should live inside the
owning `module.ingest.<area>` package. Bootstrap remains the application
composition root.

## Current Boundary Status

There are no public composition entry points for the main ingest modules yet.
Only master strategy modules currently expose composition factories:

- `module/ingest/master/extraction_strategy/composition/factory.py`
- `module/ingest/master/chunking_strategy/composition/factory.py`

The current `integration/ingest` package contains several implementation
classes, factories, and direct persistence queries. That violates the intended
direction:

```text
bootstrap
  -> module.ingest.<module>.composition
  -> application
  -> domain
  -> infrastructure

integration
  -> public module composition/contracts only
```

## Direct SQLAlchemy In Integration

These files currently use SQLAlchemy or ORM models directly and need to be
moved into owning modules or replaced by public module APIs:

- `integration/ingest/batch_finalizer.py`
- `integration/ingest/chunking/downstream_task_scheduler.py`
- `integration/ingest/chunking/extracted_asset_reader.py`
- `integration/ingest/classification/chunk_reader.py`
- `integration/ingest/embedding/chunk_reader.py`
- `integration/ingest/extraction/source_asset_reader.py`
- `integration/ingest/extraction/storage_asset_repository.py`
- factory/resolver files that instantiate repositories directly

## Known Boundary Offenders

- `integration/ingest/batch_finalizer.py`
  - Reads and updates `ChunkBatchModel` directly.
  - Should become chunking-owned batch completion service/query API.

- `integration/ingest/chunking/downstream_task_scheduler.py`
  - Reads `ChunkBatchModel` and `DocumentChunkModel` directly.
  - Instantiates embedding/classification repositories directly.
  - Should become an integration adapter that calls public embedding and
    classification scheduling APIs, while chunk lookup/default completion logic
    moves to chunking-owned services.

- `integration/ingest/extraction/source_asset_reader.py`
  - Reads `DocumentModel` and `StorageAssetModel` directly.
  - Should delegate to download/discovery-owned public reader capability.

- `integration/ingest/chunking/extracted_asset_reader.py`
  - Reads `StorageAssetModel` directly.
  - Should delegate to extraction-owned public extracted asset reader.

- `integration/ingest/embedding/chunk_reader.py`
  - Reads `DocumentChunkModel` directly.
  - Should call a chunking public query API.

- `integration/ingest/classification/chunk_reader.py`
  - Reads `DocumentChunkModel` directly.
  - Should call the same chunking public query API with classification DTO
    mapping inside the adapter.

## Ownership Migration Map

### Discovery

Move to discovery infrastructure/composition:

- `integration/ingest/discovery/data_hub_discovery_provider_resolver.py`
- `integration/ingest/discovery/data_hub_source_catalog.py`
- `integration/ingest/discovery/factory.py`

Keep as integration bridge for now:

- `integration/ingest/discovery/download_task_scheduler.py`

Target public API:

- create discovery use case
- schedule download through a download public capability, not direct download
  repository construction

### Download

Move to download infrastructure/composition:

- `integration/ingest/download/file_storage_object_storage.py`
- `integration/ingest/download/data_hub_document_source.py`
- `integration/ingest/download/factory.py`

Keep as integration bridge for now:

- `integration/ingest/download/extraction_task_scheduler.py`

Target public API:

- create download use case
- provide source asset reader capability for extraction
- schedule extraction through extraction public capability

### Extraction

Move to extraction infrastructure/composition:

- `integration/ingest/extraction/docling_extraction_engine.py`
- `integration/ingest/extraction/extraction_engine_resolver.py`
- `integration/ingest/extraction/file_storage_object_storage.py`
- `integration/ingest/extraction/storage_asset_repository.py`
- `integration/ingest/extraction/factory.py`

Refactor as integration bridge:

- `integration/ingest/extraction/source_asset_reader.py`
- `integration/ingest/extraction/chunking_task_scheduler.py`
- `integration/ingest/extraction/pending_chunking_task_scheduler.py`

Target public API:

- create extraction use case
- read extracted assets by `(ingestion_job_id, document_id)`
- schedule chunking through chunking public capability

### Chunking

Move to chunking infrastructure/composition:

- `integration/ingest/chunking/chunking_engine.py`
- `integration/ingest/chunking/chunking_engine_resolver.py`
- `integration/ingest/chunking/factory.py`

Refactor as integration bridge:

- `integration/ingest/chunking/extracted_asset_reader.py`
- `integration/ingest/chunking/downstream_task_scheduler.py`
- `integration/ingest/chunking/pending_downstream_task_scheduler.py`

Target public API:

- create chunking use case
- list chunks by batch id
- complete embedding/classification side of a batch
- schedule embedding/classification through public capabilities

### Embedding

Move to embedding infrastructure/composition:

- `integration/ingest/embedding/legacy_embedding_engine.py`
- `integration/ingest/embedding/embedding_engine_resolver.py`
- `integration/ingest/embedding/factory.py`

Refactor as integration bridge:

- `integration/ingest/embedding/chunk_reader.py`
- `integration/ingest/embedding/batch_finalizer.py`

Target public API:

- create embedding use case
- create embedding task through module-owned scheduling API
- read chunks via chunking public API
- finalize batch via chunking public API

### Classification

Move to classification infrastructure/composition:

- `integration/ingest/classification/legacy_classification_engine.py`
- `integration/ingest/classification/factory.py`

Refactor as integration bridge:

- `integration/ingest/classification/chunk_reader.py`
- `integration/ingest/classification/batch_finalizer.py`

Target public API:

- create classification use case
- create classification task through module-owned scheduling API
- read chunks via chunking public API
- finalize batch via chunking public API

### Master Configuration

Review separately:

- `integration/ingest/configuration/master_config_resolver.py`

It currently composes master repositories directly. This may belong in a master
composition API or bootstrap, depending on which caller owns the use case.

## Important Ownership Decision

`StorageAssetModel` currently lives under download infrastructure, while
extraction writes `EXTRACTED` assets and chunking reads them. Before moving
asset repository code, decide whether:

- `storage_assets` is a download-owned shared asset registry with public read
  APIs for extraction/chunking, or
- extracted assets become extraction-owned persistence behavior with a public
  extraction asset API.

Do not duplicate ORM mappings for the same table unless the architecture
explicitly accepts that tradeoff.

## Recommended Phase Order

1. Add public composition facades for each ingest module with no behavior
   change.
2. Move module-owned implementation files from `integration/ingest` into their
   owner module packages and update imports.
3. Replace integration direct ORM reads with public owner APIs.
4. Move factory wiring out of integration into module composition/bootstrap.
5. Remove unused integration files and run boundary searches.
6. Run pipeline smoke/regression checks.

## Validation Searches

Run these after each later phase:

```text
rg "from module.ingest.*.infrastructure" backend/integration/ingest
rg "from sqlalchemy|session.execute|select\\(" backend/integration/ingest
rg "StorageAssetModel|DocumentChunkModel|ChunkBatchModel|DocumentModel" backend/integration/ingest
```

## Phase 3 Update

Moved module-owned implementation files out of `integration/ingest`:

- Discovery source catalog/provider resolver moved under discovery
  infrastructure.
- Download object storage/document source moved under download
  infrastructure.
- Extraction engine/resolver/object storage/storage asset repository moved
  under extraction infrastructure.
- Chunking engine/resolver moved under chunking infrastructure.
- Embedding engine/resolver moved under embedding infrastructure.
- Classification legacy engine adapter moved under classification
  infrastructure.

The remaining files under `integration/ingest` are transitional factories and
cross-module bridges. They are intentionally left for later phases:

- Phase 4 removes direct ORM/SQLAlchemy access from integration bridges.
- Phase 5 moves/collapses transitional factories into module composition and
  bootstrap wiring.

## Phase 4 Update

Removed direct SQLAlchemy/ORM access from non-factory integration bridges:

- `integration/ingest/extraction/source_asset_reader.py`
  now delegates source asset lookup to a download-owned query contract.
- `integration/ingest/chunking/extracted_asset_reader.py`
  now delegates extracted asset lookup to an extraction-owned query contract.
- `integration/ingest/embedding/chunk_reader.py`
  now delegates chunk lookup to a chunking-owned query contract.
- `integration/ingest/classification/chunk_reader.py`
  now delegates chunk lookup to a chunking-owned query contract.
- `integration/ingest/batch_finalizer.py`
  now delegates batch completion to a chunking-owned completion contract.
- `integration/ingest/chunking/downstream_task_scheduler.py`
  no longer imports chunking ORM models or uses SQLAlchemy directly.

Added owner-side contracts and infrastructure implementations:

- `module/ingest/download/domain/contracts/source_asset_query.py`
- `module/ingest/download/infrastructure/persistence/queries/source_asset_query.py`
- `module/ingest/extraction/domain/contracts/extracted_asset_query.py`
- `module/ingest/extraction/infrastructure/persistence/queries/extracted_asset_query.py`
- `module/ingest/chunking/domain/contracts/document_chunk_query.py`
- `module/ingest/chunking/infrastructure/persistence/queries/document_chunk_query.py`
- `module/ingest/chunking/domain/contracts/chunk_batch_completion_service.py`
- `module/ingest/chunking/infrastructure/persistence/queries/chunk_batch_completion_service.py`

Remaining integration SQLAlchemy imports are only in transitional factory
files, which are Phase 5 scope.

## Phase 5 Update

Collapsed transitional factories into module composition:

- `integration/ingest/*/factory.py` files were moved into
  `module/ingest/<module>/composition/factory.py`.
- Bootstrap now imports module composition factories directly and creates
  cross-module integration bridge adapters at the application composition root.
- Module composition factories no longer import `integration.ingest`.
- Integration retains only bridge adapters such as task schedulers, chunk
  readers, asset readers, and finalizers.

Current intended dependency shape:

```text
bootstrap/modules.py
  -> module.ingest.<module>.composition.factory
  -> integration bridge adapters
  -> infrastructure implementations

module.ingest.<module>.composition.factory
  -> own application/domain/infrastructure only
```

## Phase 6 Validation

Static boundary checks passed:

- No stale imports to moved implementation files under
  `integration.ingest.*`.
- No `from integration.ingest` imports under `module/ingest`.
- No SQLAlchemy usage, `session.execute`, `select(...)`, or direct ORM model
  imports under `integration/ingest`.
- No transitional `integration/ingest/*/factory.py` files remain.
- `git diff --check` passes. The only output is Git line-ending warnings.

Runtime validation could not be executed from this sandbox because the local
venv points at a missing Python executable:

```text
No Python at "C:\Users\admin\AppData\Local\Programs\Python\Python310\python.exe"
```

Run these from the backend terminal where `(venv)` works:

```text
python -m compileall bootstrap module integration workers
python run_worker.py discovery
python run_worker.py download
python run_worker.py extraction
python run_worker.py chunking
python run_worker.py embedding
python run_worker.py classification
```

Residual architecture decision:

- `storage_assets` is still physically mapped by
  `module.ingest.download.infrastructure.persistence.models.storage_asset_model`.
- Extraction-owned storage asset repository and extracted asset query still use
  that model because SOURCE and EXTRACTED assets share the same table.
- To make module boundaries fully strict, choose a single owner for the
  `storage_assets` table/API before moving this last shared persistence concern.
