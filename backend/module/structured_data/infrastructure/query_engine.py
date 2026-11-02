from datetime import date, datetime
from decimal import Decimal
import json
import threading
import tempfile

from module.structured_data.application.query_compiler import QueryCompiler, QueryRejected, quote
from module.structured_data.domain.models import QueryResult
from .workbook import checksum


class DuckDbQueryEngine:
    def __init__(self, *, timeout_seconds=20, memory_limit='512MB', max_result_bytes=65536):
        self.compiler = QueryCompiler()
        self.timeout = timeout_seconds
        self.memory_limit = memory_limit
        self.max_bytes = max_result_bytes

    def execute(self, plan, datasets, paths):
        import duckdb
        compiled = self.compiler.compile(plan, datasets)
        files = []
        for dataset in compiled.datasets:
            path = paths.get(dataset.id)
            if path is None or not path.is_file() or checksum(path) != dataset.parquet_sha256:
                raise QueryRejected('Parquet artifact is missing or its checksum does not match the catalog')
            files.append(str(path.resolve()))
        spill = tempfile.TemporaryDirectory(prefix='xlsx-query-spill-')
        connection = duckdb.connect(':memory:', config={'threads': 2, 'memory_limit': self.memory_limit,
            'temp_directory':spill.name})
        timer = threading.Timer(self.timeout, connection.interrupt)
        timer.daemon = True
        try:
            timer.start()
            literals = ','.join("'"+path.replace("'","''")+"'" for path in files)
            connection.execute(f'SET allowed_paths = [{literals}]')
            connection.execute('SET enable_external_access = false')
            for index,group in enumerate(compiled.bindings):
                parts = []
                for dataset in group:
                    path = str(paths[dataset.id].resolve()).replace("'", "''")
                    parts.append(f"SELECT *, '{dataset.id}' AS __dataset_id FROM read_parquet('{path}')")
                # Paths are verified local artifacts, never model output. UNION ALL
                # preserves duplicate source records across sheets.
                connection.execute(f'CREATE TEMP VIEW d{index} AS ' + ' UNION ALL '.join(parts))
            for alias,key in compiled.join_checks:
                duplicate = connection.execute(f'SELECT 1 FROM {quote(alias)} WHERE {quote(key)} IS NOT NULL GROUP BY {quote(key)} HAVING count(*) > 1 LIMIT 1').fetchone()
                if duplicate:
                    raise QueryRejected('Join right-hand keys are not unique; a many-to-many join could inflate statistics')
            cursor = connection.execute(compiled.sql, compiled.parameters)
            columns = tuple(item[0] for item in cursor.description)
            values = cursor.fetchmany(compiled.limit+1)
            truncated = len(values) > compiled.limit
            values = values[:compiled.limit]
            hidden = 2*len(compiled.bindings) if not compiled.aggregated else 0
            if hidden:
                columns = columns[:-hidden]
            def encode(value):
                if isinstance(value,(datetime,date)):
                    return value.isoformat()
                if isinstance(value,Decimal):
                    return float(value)
                return value
            rows, row_sources, size = [], [], 0
            for row in values:
                data = tuple(encode(v) for v in (row[:-hidden] if hidden else row))
                payload_size = len(json.dumps(data,ensure_ascii=False,allow_nan=False).encode('utf8'))
                if size + payload_size > self.max_bytes:
                    truncated = True
                    break
                size += payload_size
                rows.append(data)
                if hidden:
                    row_sources.append({str(row[-hidden+2*i+1]):row[-hidden+2*i]
                        for i in range(len(compiled.bindings)) if row[-hidden+2*i+1] is not None})
            sources = tuple({'dataset_id':str(dataset.id),'document_id':str(dataset.document_id),
                'version':dataset.version,'file_name':dataset.file_name,'sheet':dataset.sheet,
                'range':dataset.source_range,'warnings':list(dataset.warnings)} for dataset in compiled.datasets)
            return QueryResult(columns,tuple(rows),sources,truncated,plan,compiled.chart,tuple(row_sources),compiled.column_metadata)
        except duckdb.InterruptException as error:
            raise QueryRejected('Structured query exceeded its execution time budget') from error
        except duckdb.OutOfMemoryException as error:
            raise QueryRejected('Structured query exceeded its memory budget') from error
        finally:
            timer.cancel()
            timer.join()
            connection.close()
            spill.cleanup()
