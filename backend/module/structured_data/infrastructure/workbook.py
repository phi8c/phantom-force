"""Stream workbook rows into typed Parquet; source row identity is never inferred."""
from collections import Counter
from dataclasses import replace
from datetime import date, datetime, time
import hashlib
import json
import math
from pathlib import Path
import posixpath
import re
from uuid import NAMESPACE_URL, uuid5
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from module.structured_data.domain.models import BuiltDataset, Column, Dataset


def checksum(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def json_value(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return value


def _kind(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, datetime):
        return 'datetime'
    if isinstance(value, date):
        return 'date'
    if isinstance(value, time):
        return 'string'
    if isinstance(value, int):
        return 'integer' if -(2**63) <= value < 2**63 else 'string'
    if isinstance(value, float) and math.isfinite(value):
        return 'number'
    return 'string'


def _metadata(source, max_bytes):
    """Read named table/merge metadata without loading worksheet cell trees."""
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    rel = '{http://schemas.openxmlformats.org/package/2006/relationships}'
    rid = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    result = {}
    with ZipFile(source) as archive:
        if sum(item.file_size for item in archive.infolist()) > max_bytes:
            raise ValueError('Workbook uncompressed size exceeds the extraction budget')
        relations = {e.get('Id'): e.get('Target') for e in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        root = ET.fromstring(archive.read('xl/workbook.xml'))
        for sheet in root.findall(ns + 'sheets/' + ns + 'sheet'):
            target = relations[sheet.get(rid)]
            path = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            parts, merges = [], []
            with archive.open(path) as stream:
                stack = []
                for event, element in ET.iterparse(stream, events=('start', 'end')):
                    if event == 'start':
                        stack.append(element)
                        continue
                    if element.tag == ns + 'tablePart':
                        parts.append(element.get(rid))
                    elif element.tag == ns + 'mergeCell':
                        merges.append(element.get('ref'))
                    if len(stack) > 1:
                        stack[-2].remove(element)
                    element.clear()
                    stack.pop()
            tables = []
            relpath = posixpath.join(posixpath.dirname(path), '_rels', posixpath.basename(path) + '.rels')
            if parts and relpath in archive.namelist():
                links = {e.get('Id'): e.get('Target') for e in ET.fromstring(archive.read(relpath))
                         if e.tag == rel + 'Relationship' and e.get('TargetMode') != 'External'}
                for part in parts:
                    link = links.get(part)
                    if not link:
                        raise ValueError('Workbook table relationship is unavailable')
                    tablepath = link.lstrip('/') if link.startswith('/') else posixpath.normpath(posixpath.dirname(path) + '/' + link)
                    table = ET.fromstring(archive.read(tablepath))
                    tables.append({'range': table.get('ref'), 'name': table.get('displayName'),
                                   'header_rows': int(table.get('headerRowCount', '1')),
                                   'totals_rows': int(table.get('totalsRowCount', '0'))})
            result[sheet.get('name')] = {'tables': tables, 'merges': merges, 'hidden': sheet.get('state', 'visible') != 'visible'}
    return result


class XlsxWorkbookBuilder:
    def build(self, source, output, *, space, document, file_name, configuration):
        import openpyxl
        from openpyxl.utils.cell import range_boundaries, get_column_letter
        output.mkdir(parents=True, exist_ok=True)
        version = checksum(source)
        metadata = _metadata(source, int(configuration.get('max_uncompressed_bytes',512*1024*1024)))
        cached = openpyxl.load_workbook(source, read_only=True, data_only=True, keep_links=False)
        formulas = openpyxl.load_workbook(source, read_only=True, data_only=False, keep_links=False)
        built = []
        skipped = []
        try:
            overrides = configuration.get('ranges', [])
            if not isinstance(overrides, list) or any(not isinstance(v,dict) or not isinstance(v.get('sheet'),str) or not isinstance(v.get('range'),str) for v in overrides):
                raise ValueError('structured_data.ranges must contain objects with sheet and range strings')
            for sheet in formulas:
                if configuration.get('include_sheets') and sheet.title not in configuration['include_sheets']:
                    continue
                info = metadata[sheet.title]
                if info['hidden'] and not configuration.get('include_hidden', False):
                    if any(v.get('sheet') == sheet.title for v in overrides):
                        raise ValueError('Explicit hidden-sheet ranges require include_hidden=true')
                    continue
                regions = [dict(v) for v in overrides if v.get('sheet') == sheet.title]
                if not regions:
                    regions = info['tables'] or self._detect(sheet, int(configuration.get('max_cells', 5_000_000)))
                if not regions:
                    skipped.append(sheet.title)
                occupied = []
                for region in regions:
                    if len(built) >= 32:
                        raise ValueError('At most 32 datasets per workbook are supported; narrow include_sheets/ranges')
                    bounds = range_boundaries(region['range'])
                    x1, y1, x2, y2 = bounds
                    if min(bounds) < 1 or x2 < x1 or y2 <= y1:
                        raise ValueError(f'Invalid/empty dataset range in {sheet.title}')
                    if any(not (x2 < a or c < x1 or y2 < b or d < y1) for a,b,c,d in occupied):
                        raise ValueError('Overlapping dataset ranges are ambiguous')
                    occupied.append(bounds)
                    headers = int(region.get('header_rows', 1))
                    if not 1 <= headers <= 10 or y1 + headers > y2 + 1:
                        raise ValueError('Dataset needs one to ten explicit header rows')
                    for merged in info['merges']:
                        a,b,c,d = range_boundaries(merged)
                        if not (c < x1 or a > x2 or d < y1 or b > y2) and d >= y1 + headers:
                            raise ValueError(f'Merged data cells require review: {sheet.title}!{merged}')
                    result = self._build_region(sheet, cached[sheet.title], region, output,
                        space, document, file_name, version, configuration, info['merges'])
                    built.append(result)
            missing = {r.get('sheet') for r in overrides} - set(formulas.sheetnames)
            if missing:
                raise ValueError(f'Configured sheets not found: {sorted(missing)}')
            if not built:
                raise ValueError('Workbook has no readable tabular datasets; configure structured_data.ranges')
            built = self._relationships(built,configuration.get('relationships',[]))
            if skipped:
                warning = 'No table detected in sheets: '+', '.join(skipped)+'; configure ranges to include them'
                built = [replace(value,dataset=replace(value.dataset,warnings=(*value.dataset.warnings,warning))) for value in built]
            return built
        finally:
            cached.close()
            formulas.close()

    def _relationships(self, built, specifications):
        if not isinstance(specifications,list) or len(specifications) > 64:
            raise ValueError('At most 64 explicit dataset relationships are supported')
        links = {value.dataset.id:[] for value in built}
        for spec in specifications:
            if not isinstance(spec,dict) or spec.get('cardinality','many_to_one') != 'many_to_one':
                raise ValueError('Only explicitly configured many_to_one relationships are supported')
            def find(sheet, source_range):
                values = [value.dataset for value in built if value.dataset.sheet == sheet and
                          (source_range is None or value.dataset.source_range == source_range)]
                if len(values) != 1:
                    raise ValueError('Relationship sheet/range must identify exactly one dataset')
                return values[0]
            left = find(spec.get('left_sheet'),spec.get('left_range'))
            right = find(spec.get('right_sheet'),spec.get('right_range'))
            def key(dataset, name):
                values = [column.key for column in dataset.columns if name in {column.key,column.name}]
                if len(values) != 1:
                    raise ValueError('Relationship column is unavailable or ambiguous')
                return values[0]
            if left.id == right.id:
                raise ValueError('Self relationships are not supported')
            links[left.id].append({'dataset_id':str(right.id),'left_column':key(left,spec.get('left_column')),
                                   'right_column':key(right,spec.get('right_column'))})
        return [replace(value,dataset=replace(value.dataset,relationships=tuple(links[value.dataset.id]))) for value in built]

    def _detect(self, sheet, max_cells):
        from openpyxl.utils.cell import get_column_letter
        # A blank row separates independent tables; explicit ranges cover other layouts.
        if sheet.max_row and sheet.max_column and sheet.max_row * sheet.max_column > max_cells:
            raise ValueError('Worksheet dimensions exceed the detection budget; configure explicit ranges')
        regions, active = [], None
        visited = 0
        for row_index, row in enumerate(sheet.iter_rows(), start=1):
            visited += max(len(row),1)
            if visited > max_cells:
                raise ValueError('Worksheet scan exceeds the detection cell budget')
            present = [cell.column for cell in row if cell.value is not None and str(cell.value).strip()]
            if not present:
                if active:
                    active['end'] = row_index - 1
                    regions.append(active)
                    active = None
                continue
            if active is None:
                # Standalone titles/notes are not a reliable tabular header.
                if len(present) < 2:
                    continue
                if any(not isinstance(row[index-1].value,str) for index in present):
                    continue
                if present != list(range(min(present), max(present) + 1)):
                    raise ValueError(f'Ambiguous horizontal tables in {sheet.title}; configure explicit ranges')
                active = {'start': row_index, 'left': min(present), 'right': max(present), 'end': row_index}
            elif min(present) < active['left'] or max(present) > active['right']:
                raise ValueError(f'Data extends outside inferred header in {sheet.title}; configure explicit ranges')
            active['end'] = row_index
        if active:
            regions.append(active)
        return [{'range': f"{get_column_letter(r['left'])}{r['start']}:{get_column_letter(r['right'])}{r['end']}",
                 'header_rows': 1, 'inferred': True} for r in regions if r['end'] > r['start']]

    def _build_region(self, sheet, cached, region, output, space, document, file_name, version, settings, merges):
        import pyarrow as pa
        import pyarrow.parquet as pq
        from openpyxl.utils.cell import range_boundaries
        x1,y1,x2,y2 = range_boundaries(region['range'])
        if (x2-x1+1)*(y2-y1+1) > int(settings.get('max_cells', 5_000_000)):
            raise ValueError('Dataset exceeds configured cell budget')
        header_rows = int(region.get('header_rows', 1))
        end = y2 - int(region.get('totals_rows', 0))
        if end < y1 + header_rows:
            raise ValueError('Dataset has no data rows')
        recipe = json.dumps({'abi':1,'region':region,'arrow':pa.__version__,
                             'reader':__import__('openpyxl').__version__},sort_keys=True)
        identifier = uuid5(NAMESPACE_URL, f'{space}:{document}:{version}:{sheet.title}:{recipe}')
        spool, parquet, formula_file = [output / (str(identifier) + suffix) for suffix in ('.jsonl', '.parquet', '.formulas.jsonl')]
        width = x2-x1+1
        if width > 256:
            raise ValueError('Dataset has more than 256 columns; configure a narrower range')
        labels = [[] for _ in range(width)]
        header_cells = {}
        for row in sheet.iter_rows(min_row=y1, max_row=y1+header_rows-1, min_col=x1, max_col=x2):
            for cell in row:
                if cell.value is not None:
                    header_cells[(cell.row, cell.column)] = str(cell.value)
        for merge in merges:
            a,b,c,d = range_boundaries(merge)
            if y1 <= b <= d < y1+header_rows:
                text = header_cells.get((b,a))
                if text:
                    for column in range(max(a,x1), min(c,x2)+1):
                        header_cells[(b,column)] = text
        for (row,column), text in sorted(header_cells.items()):
            labels[column-x1].append(text)
        full_names = [' / '.join(parts) or f'Column {i+1}' for i,parts in enumerate(labels)]
        names = [name[:256] for name in full_names]
        if any(not parts for parts in labels):
            raise ValueError(f'Empty header in {sheet.title}; configure header_rows/range')
        keys, seen = [], Counter()
        for index, name in enumerate(names):
            key = re.sub(r'[^\w]+', '_', name.strip().lower(), flags=re.UNICODE).strip('_')[:55] or f'column_{index+1}'
            if key.startswith('__') or key[0].isdigit():
                key = 'c_' + key
            seen[key] += 1
            keys.append(key if seen[key] == 1 else f'{key}_{seen[key]}')
        # Catch collisions with already-suffixed source names too.
        if len(set(keys)) != width:
            keys = [f'c{i+1}_{key}' for i,key in enumerate(keys)]
        types = [set() for _ in keys]
        stats = [{'null_count': 0, 'min': None, 'max': None} for _ in keys]
        distinct = [set() for _ in keys]
        formats = [None] * width
        warnings = []
        if any(len(name) > 256 for name in full_names):
            warnings.append('Long column display names truncated to 256 characters; original headers remain in the source workbook')
        formula_count = missing_formula = rows = 0
        if region.get('inferred'):
            warnings.append('Range/header inferred from contiguous nonempty rows; explicit ranges are recommended for reports with subtotals')
        with spool.open('w', encoding='utf8') as data_out, formula_file.open('w', encoding='utf8') as formula_out:
            left = sheet.iter_rows(min_row=y1+header_rows, max_row=end, min_col=x1, max_col=x2)
            right = cached.iter_rows(min_row=y1+header_rows, max_row=end, min_col=x1, max_col=x2)
            for row_index, (original, values) in enumerate(zip(left, right, strict=True), start=y1+header_rows):
                data = []
                for i,(cell,value_cell) in enumerate(zip(original, values, strict=True)):
                    value = value_cell.value
                    if cell.data_type == 'f':
                        formula_count += 1
                        if value is None:
                            missing_formula += 1
                        formula_out.write(json.dumps({'cell': cell.coordinate, 'formula': cell.value,
                            'cached_value': json_value(value)}, ensure_ascii=False) + '\n')
                    if cell.data_type == 'e' or value_cell.data_type == 'e':
                        warnings.append(f'Excel error at {cell.coordinate}; retained as text')
                        value = str(value)
                    kind = _kind(value)
                    if kind:
                        types[i].add(kind)
                    formats[i] = formats[i] or (getattr(cell, 'number_format', '')[:256] or None)
                    item = json_value(value)
                    data.append(item)
                    if item is None:
                        stats[i]['null_count'] += 1
                if all(value is None for value in data):
                    for item in stats:
                        item['null_count'] -= 1
                    continue
                # Unmarked summary rows are ambiguous: never double-count by guessing.
                if region.get('inferred') and any(isinstance(v,str) and re.fullmatch(r'(grand\s+)?total|subtotal|tổng(\s+cộng)?', v.strip(), re.IGNORECASE) for v in data):
                    raise ValueError(f'Unmarked totals in {sheet.title}; use an Excel Table or explicit range excluding totals')
                data_out.write(json.dumps({'row': row_index, 'values': data}, ensure_ascii=False, allow_nan=False) + '\n')
                rows += 1
        if missing_formula:
            raise ValueError(f'{sheet.title} has {missing_formula} formulas without cached values; recalculate/save the workbook before ingestion')
        if not rows:
            raise ValueError('Dataset has no nonempty records')
        kinds = [('number' if values <= {'integer','number'} and 'number' in values else
                  next(iter(values)) if len(values) == 1 else 'string') for values in types]
        arrow_types = {'integer': pa.int64(), 'number': pa.float64(), 'boolean': pa.bool_(),
                       'date': pa.date32(), 'datetime': pa.timestamp('us'), 'string': pa.string()}
        schema = pa.schema([pa.field(key, arrow_types[kind]) for key,kind in zip(keys,kinds)] + [pa.field('__source_row', pa.int64())])
        def normalize(value, kind):
            if value is None:
                return None
            if kind == 'string':
                return str(value)
            if kind == 'date':
                return date.fromisoformat(value)
            if kind == 'datetime':
                return datetime.fromisoformat(value)
            if kind == 'number':
                return float(value)
            return value
        with pq.ParquetWriter(parquet, schema, compression='zstd', write_statistics=True) as writer, spool.open(encoding='utf8') as incoming:
            batch = []
            for line in incoming:
                raw = json.loads(line)
                record = {key: normalize(value,kind) for key,value,kind in zip(keys,raw['values'],kinds)}
                record['__source_row'] = raw['row']
                batch.append(record)
                for i,key in enumerate(keys):
                    value = record[key]
                    if value is not None:
                        encoded = json_value(value)
                        canonical = 0.0 if isinstance(value,(int,float)) and not isinstance(value,bool) and value == 0 else encoded
                        if len(distinct[i]) <= 256:
                            distinct[i].add(hashlib.sha256(str(canonical).encode('utf8')).digest())
                        if stats[i]['min'] is None or encoded < stats[i]['min']:
                            stats[i]['min'] = encoded
                        if stats[i]['max'] is None or encoded > stats[i]['max']:
                            stats[i]['max'] = encoded
                if len(batch) >= 4096:
                    writer.write_table(pa.Table.from_pylist(batch, schema=schema), row_group_size=4096)
                    batch = []
            if batch:
                writer.write_table(pa.Table.from_pylist(batch, schema=schema), row_group_size=4096)
        spool.unlink()
        for i,value in enumerate(stats):
            if kinds[i] == 'string':
                for key in ('min','max'):
                    if isinstance(value[key],str) and len(value[key]) > 160:
                        value[key] = value[key][:160]
                        value['extrema_truncated'] = True
            value['distinct_count'] = len(distinct[i]) if len(distinct[i]) <= 256 else None
            value['distinct_count_capped'] = len(distinct[i]) > 256
        if any(len(t) > 1 and not t <= {'integer','number'} for t in types):
            warnings.append('Mixed-type columns preserved as strings; numeric coercion was not guessed')
        prefix = f'structured/{space}/{document}/{version}/{identifier}'
        dataset = Dataset(identifier, space, document, version, file_name, sheet.title, region['range'],
            str(region.get('name') or f'{file_name} / {sheet.title} / {region["range"]}')[:500],
            tuple(Column(k,n,t,x1+i,stats[i],formats[i],
                (str(region.get('column_descriptions',{}).get(k) or region.get('column_descriptions',{}).get(n) or '')[:500] or None))
                for i,(k,n,t) in enumerate(zip(keys,names,kinds))),
            rows, prefix + '.parquet', checksum(parquet), tuple(dict.fromkeys(warnings)),
            prefix + '.formulas.jsonl' if formula_count else None,
            str(region.get('description') or f'Tabular statistics from {file_name}, worksheet {sheet.title}')[:1000])
        if not formula_count:
            formula_file.unlink()
        return BuiltDataset(dataset, parquet, formula_file if formula_count else None)
