import json
import os
from pathlib import Path

from shared.ingestion.parts import ExtractionManifest
from module.ingest.extraction.infrastructure.normalization.document_codec import decode_document
from module.ingest.extraction.infrastructure.normalization.structure_rules import APPLIED_WARNING


def _rules_applied(payload: dict) -> bool:
    return APPLIED_WARNING in payload['extraction'].get('warnings', ())


def _remapped_parts(directory: Path, manifest: ExtractionManifest, level_map: dict[int, int]):
    order = 0
    stack = []
    for part in manifest.parts:
        payload = json.loads((directory / part.artifact_path).read_text(encoding='utf-8'))
        if payload.get('empty_part'):
            continue
        decode_document(payload)
        prefix = part.id + ':'
        local_sections = {section['id']: section for section in payload['sections']}
        compact = _rules_applied(payload)
        sections = []
        for block in payload['blocks']:
            if block['kind'] == 'heading' and block['section_id'] is not None:
                section = local_sections[block['section_id']]
                level = level_map[section['level']] if compact else section['level']
                while stack and stack[-1]['level'] >= level:
                    stack.pop()
                section = {**section, 'id': prefix + section['id'], 'level': level,
                           'parent_id': stack[-1]['id'] if stack else None}
                stack.append(section)
                sections.append(section)
            block['id'] = prefix + block['id']
            block['order'] = order
            order += 1
            block['section_id'] = stack[-1]['id'] if stack else None
            if block['table_id']:
                block['table_id'] = prefix + block['table_id']
            _source(block['source'], part, manifest.source_unit)
        for table in payload['tables']:
            table['id'] = prefix + table['id']
            _source(table['source'], part, manifest.source_unit)
        payload['sections'] = sections
        yield payload


def _source(source, part, unit):
    source['part_id'] = part.id
    if unit == 'page' and source.get('page_number') is not None:
        if not 1 <= source['page_number'] <= part.source_end - part.source_start + 1:
            raise ValueError('Part page reference falls outside its source range')
        source['page_number'] += part.source_start - 1
    if unit == 'native_block' and source.get('native_block_index') is not None:
        if not 0 <= source['native_block_index'] <= part.source_end - part.source_start:
            raise ValueError('Part block reference falls outside its source range')
        source['native_block_index'] += part.source_start


def assemble(directory: Path, manifest: ExtractionManifest, engine: str, document_title: str | None = None) -> tuple[dict, Path]:
    if not manifest.completed:
        raise ValueError('Cannot assemble an incomplete manifest')
    count = 0
    warnings = set()
    structured = False
    title = None
    versions = set()
    rule_levels = set()
    for part in manifest.parts:
        payload = json.loads((directory / part.artifact_path).read_text(encoding='utf-8'))
        warnings.update(payload['extraction'].get('warnings', ()))
        if payload.get('empty_part'):
            warnings.add(f'No readable text/table content in {part.id}; blank or image-only range')
            continue
        decode_document(payload)
        part_title = payload.get('title')
        if title is None and isinstance(part_title, str) and part_title.strip():
            if Path(part_title).stem != part.id and part_title.strip().lower() not in {'untitled', 'document', 'extracted document'}:
                title = part_title.strip()
        version = payload['extraction'].get('engine_version')
        if isinstance(version, str) and version:
            versions.add(version)
        count += len(payload['blocks'])
        structured = structured or bool(payload['sections'])
        if _rules_applied(payload):
            rule_levels.update(section['level'] for section in payload['sections'])
    if not count:
        raise ValueError('Entire document contains no supported text/table content')
    header = {
        'schema_version': 2, 'document_id': manifest.document_id, 'title': title or document_title or 'Extracted document',
        'extraction': {'engine': engine, 'engine_version': ','.join(sorted(versions)) or 'unknown',
                       'structure_quality': 'partial' if structured else 'flat',
                       'warnings': sorted(warnings)},
        'multipart': {'part_count': len(manifest.parts), 'source_checksum': manifest.source_checksum,
                      'configuration_fingerprint': manifest.configuration_fingerprint,
                      'source_unit': manifest.source_unit},
    }
    # Rule ranks are sparse; close the gaps once so "Chương > Điều" stays levels 1 > 2 across parts.
    level_map = {level: rank for rank, level in enumerate(sorted(rule_levels), 1)}
    target = directory / 'assembled.json'
    temporary = directory / 'assembled.json.tmp'
    with temporary.open('w', encoding='utf-8') as stream:
        # This header line may be replaced with the actual document UUID on upload.
        stream.write(json.dumps(header, ensure_ascii=False)[:-1] + ',\n')
        for array_index, name in enumerate(('blocks', 'tables', 'sections', 'legacy_sections')):
            if array_index:
                stream.write(',')
            stream.write(json.dumps(name) + ':[')
            first = True
            for payload in _remapped_parts(directory, manifest, level_map):
                if name == 'legacy_sections':
                    tables = {table['id']: table for table in payload['tables']}
                    values = []
                    for block in payload['blocks']:
                        content = (json.dumps(tables[block['table_id']], ensure_ascii=False)
                                   if block['table_id'] else block['text'])
                        values.append({'id': block['id'], 'title': block['text'] if block['kind'] == 'heading' else 'ROOT',
                                       'level': 2, 'content': content, 'aggregated_content': content,
                                       'token_count': len(content.split()), 'aggregated_token_count': len(content.split()),
                                       'page_no': block['source'].get('page_number'), 'tables': [], 'children': [], 'images': []})
                else:
                    values = payload[name]
                for value in values:
                    if not first:
                        stream.write(',')
                    json.dump(value, stream, ensure_ascii=False)
                    first = False
            stream.write(']')
        stream.write('}')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, target)
    return header, target
