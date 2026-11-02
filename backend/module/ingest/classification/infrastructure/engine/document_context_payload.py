"""Bounded document-context projection; never requires a V2 legacy tree."""
import json

from shared.ingestion.json_items import JsonObjectItems


class DocumentContextPayloadReader:
    def __init__(self, *, max_headings=100, max_heading_chars=160, max_sample_chars=4000):
        self.max_headings = max_headings
        self.max_heading_chars = max_heading_chars
        self.max_sample_chars = max_sample_chars

    def read(self, path):
        with path.open(encoding='utf-8-sig') as stream:
            version = 1
            for kind, key, value in JsonObjectItems(stream, arrays=set()).items():
                if kind == 'field' and key == 'schema_version':
                    version = value
        if type(version) is not int or version not in {1, 2}:
            raise ValueError('Unsupported extraction schema version')
        if version == 1:
            # Legacy trees retain their historical memory unit; new assets use V2.
            with path.open(encoding='utf-8-sig') as stream:
                return json.load(stream)

        headings, samples = [], []
        remaining = self.max_sample_chars
        title = file_name = None
        block_count = table_count = 0

        def sample(text):
            nonlocal remaining
            if remaining > 0 and isinstance(text, str) and text.strip():
                value = text[:remaining]
                samples.append(value)
                remaining -= len(value)

        with path.open(encoding='utf-8-sig') as stream:
            parser = JsonObjectItems(stream, fields={'title', 'file_name', 'schema_version'})
            for kind, key, value in parser.items():
                if kind == 'field' and key in {'title', 'file_name'}:
                    if value is not None and not isinstance(value, str):
                        raise ValueError('Document title/file_name must be text')
                    if key == 'title':
                        title = value[:self.max_heading_chars] if value else None
                    else:
                        file_name = value[:self.max_heading_chars] if value else None
                elif kind == 'item' and key == 'sections':
                    if not isinstance(value, dict):
                        raise ValueError('Invalid V2 section')
                    heading = value.get('title')
                    if len(headings) < self.max_headings and isinstance(heading, str) and heading.strip().upper() != 'ROOT':
                        if heading.strip():
                            headings.append({'title': heading.strip()[:self.max_heading_chars], 'level': value.get('level')})
                elif kind == 'item' and key == 'blocks':
                    if not isinstance(value, dict):
                        raise ValueError('Invalid V2 block')
                    block_count += 1
                    sample(value.get('text'))
                elif kind == 'item' and key == 'tables':
                    if not isinstance(value, dict) or not isinstance(value.get('cells'), list):
                        raise ValueError('Invalid V2 table')
                    table_count += 1
                    sample(value.get('caption'))
                    for cell in value['cells']:
                        if not isinstance(cell, dict):
                            raise ValueError('Invalid V2 cell')
                        sample(cell.get('text'))
        if not block_count:
            raise ValueError('V2 extraction has no blocks')
        return {
            'schema_version': 2, 'title': title, 'file_name': file_name,
            'sections': headings, 'content': '\n'.join(samples)[:self.max_sample_chars],
            'content_sample_is_partial': True, 'block_count': block_count, 'table_count': table_count,
        }
