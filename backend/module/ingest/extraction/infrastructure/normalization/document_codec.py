"""Typed decoding at the persisted artifact boundary."""
from shared.ingestion.document import (
    BlockKind, ContentBlock, DocumentSection, ExtractedDocumentV2, ExtractedTable,
    ExtractionMetadata, SourceLocation, StructureQuality, TableCell,
)


def decode_document(payload: dict) -> ExtractedDocumentV2:
    metadata = payload['extraction']
    return ExtractedDocumentV2(
        document_id=payload['document_id'], title=payload['title'],
        schema_version=payload['schema_version'],
        extraction=ExtractionMetadata(**{**metadata, 'structure_quality': StructureQuality(metadata['structure_quality']),
                                         'warnings': tuple(metadata.get('warnings', ())) }),
        blocks=tuple(ContentBlock(**{**block, 'kind': BlockKind(block['kind']),
                                      'source': SourceLocation(**block['source'])}) for block in payload['blocks']),
        tables=tuple(ExtractedTable(**{**table, 'source': SourceLocation(**table['source']),
                                      'cells': tuple(TableCell(**cell) for cell in table['cells']),
                                      'header_rows': tuple(table['header_rows']) if table.get('header_rows') is not None else None})
                     for table in payload.get('tables', ())),
        sections=tuple(DocumentSection(**section) for section in payload.get('sections', ())),
    )
