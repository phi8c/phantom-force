"""Validate a small relational plan and compile only whitelisted operations."""
from dataclasses import dataclass
from datetime import date, datetime
import math
import re
from uuid import UUID

from module.structured_data.domain.models import Dataset


class QueryRejected(ValueError):
    pass


def quote(value):
    return '"' + value.replace('"', '""') + '"'


def percentage_format(value):
    quoted = escaped = False
    for character in value or '':
        if escaped:
            escaped = False
        elif character == '\\':
            escaped = True
        elif character == '"':
            quoted = not quoted
        elif character == '%' and not quoted:
            return True
    return False


@dataclass(frozen=True)
class CompiledPlan:
    sql: str
    parameters: tuple
    datasets: tuple[Dataset, ...]
    join_checks: tuple[tuple[str, str], ...]
    limit: int
    aggregated: bool
    chart: dict | None
    bindings: tuple[tuple[Dataset, ...], ...]
    column_metadata: dict


class QueryCompiler:
    def compile(self, plan, candidates):
        if not isinstance(plan, dict) or set(plan) - {'dataset_id','union_dataset_ids','joins','select','filters','order_by','limit','chart'}:
            raise QueryRejected('Unsupported query plan fields; raw SQL is not accepted')
        allowed = {str(item.id): item for item in candidates}
        base = allowed.get(str(plan.get('dataset_id')))
        if base is None:
            raise QueryRejected('Unknown or unauthorized base dataset')
        datasets = [base]
        base_group = [base]
        union_ids = plan.get('union_dataset_ids', [])
        if not isinstance(union_ids,list) or len(union_ids) > 31:
            raise QueryRejected('At most 32 same-schema datasets can be unioned')
        for identity in union_ids:
            item = allowed.get(str(identity))
            if item is None or item.id in {d.id for d in base_group}:
                raise QueryRejected('Unavailable or duplicated union dataset')
            compatible = len(item.columns) == len(base.columns) and all(
                a.key == b.key and a.number_format == b.number_format and
                (a.data_type == b.data_type or {a.data_type,b.data_type} <= {'integer','number'})
                for a,b in zip(base.columns,item.columns))
            if item.document_id != base.document_id or item.version != base.version or not compatible:
                raise QueryRejected('Union datasets must have identical schemas/units and the same workbook version')
            base_group.append(item)
        bindings = [tuple(base_group)]
        joins, checks, parameters = [], [], []
        aliases = {'d0': {column.key: column for column in base.columns}}

        def column(reference):
            if not isinstance(reference, str):
                raise QueryRejected('Column must reference dN.column_key')
            pieces = reference.split('.', 1)
            alias, key = pieces if len(pieces) == 2 else ('d0', reference)
            found = aliases.get(alias, {}).get(key)
            if found is None:
                raise QueryRejected(f'Unknown column: {reference}')
            return f'{quote(alias)}.{quote(key)}', found, alias

        join_specs = plan.get('joins', [])
        if not isinstance(join_specs, list) or len(join_specs) > 2:
            raise QueryRejected('At most two joins are supported')
        for index, spec in enumerate(join_specs, start=1):
            if not isinstance(spec, dict) or set(spec) - {'dataset_id','left_column','right_column','type'}:
                raise QueryRejected('Invalid join')
            right = allowed.get(str(spec.get('dataset_id')))
            if right is None or right.id in {item.id for item in datasets}:
                raise QueryRejected('Join dataset is unavailable or duplicated')
            if right.document_id != base.document_id or right.version != base.version:
                raise QueryRejected('Joins must stay within the same workbook version')
            left_expr, left_col, left_alias = column(spec.get('left_column'))
            alias = f'd{index}'
            aliases[alias] = {c.key:c for c in right.columns}
            right_key = spec.get('right_column')
            right_expr, right_col, _ = column(f'{alias}.{right_key}')
            for left_dataset in bindings[int(left_alias[1:])]:
                if not any(link.get('dataset_id') == str(right.id) and link.get('left_column') == left_col.key
                           and link.get('right_column') == right_key for link in left_dataset.relationships):
                    raise QueryRejected('Join relationship has not been explicitly confirmed in workbook configuration')
            if left_col.data_type != right_col.data_type:
                raise QueryRejected('Join key types must match')
            join_type = spec.get('type', 'left')
            if not isinstance(join_type,str) or join_type not in {'left', 'inner'}:
                raise QueryRejected('Only left/inner joins are supported')
            joins.append(f'{join_type.upper()} JOIN {quote(alias)} ON {left_expr} = {right_expr}')
            checks.append((alias, right_key))
            datasets.append(right)
            bindings.append((right,))

        selections = plan.get('select')
        if not isinstance(selections, list) or not 1 <= len(selections) <= 30:
            raise QueryRejected('Select between 1 and 30 expressions')
        expressions, dimensions, output = [], [], {}
        metadata = {}
        aggregated = any(isinstance(s,dict) and s.get('aggregate') for s in selections)
        for spec in selections:
            if not isinstance(spec,dict) or set(spec) - {'column','aggregate','alias','time_grain'}:
                raise QueryRejected('Invalid select expression')
            alias = spec.get('alias')
            if not isinstance(alias,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,62}',alias) or alias.startswith('__') or alias in output:
                raise QueryRejected('Output aliases must be unique simple identifiers')
            aggregate = spec.get('aggregate')
            if aggregate is not None and (not isinstance(aggregate,str) or aggregate not in {'sum','avg','min','max','count','count_distinct'}):
                raise QueryRejected('Unsupported aggregation')
            if aggregate == 'count' and spec.get('column') is None:
                expression, kind = '*', 'integer'
                number_format = None
            else:
                expression, selected, _ = column(spec.get('column'))
                kind = selected.data_type
                number_format = selected.number_format
            grain = spec.get('time_grain')
            if grain is not None:
                if not isinstance(grain,str) or grain not in {'day','month','year'} or kind not in {'date','datetime'} or aggregate:
                    raise QueryRejected('Time grouping requires a date/datetime dimension')
                expression = f"date_trunc('{grain}', {expression})"
            if aggregate:
                functions = {'sum':'sum','avg':'avg','min':'min','max':'max','count':'count','count_distinct':'count'}
                if aggregate not in functions:
                    raise QueryRejected('Unsupported aggregation')
                if aggregate in {'sum','avg'} and kind not in {'integer','number'}:
                    raise QueryRejected('SUM/AVG require a numeric source column')
                prefix = 'DISTINCT ' if aggregate == 'count_distinct' else ''
                expression = f'{functions[aggregate]}({prefix}{expression})'
                if aggregate in {'count','count_distinct'}:
                    kind = 'integer'
                    number_format = None
                elif aggregate == 'avg':
                    kind = 'number'
            else:
                dimensions.append(expression)
            output[alias] = kind
            metadata[alias] = {'data_type':kind,'number_format':number_format,
                               'source_column':spec.get('column'),'aggregate':aggregate,
                               'percentage':percentage_format(number_format)}
            expressions.append(f'{expression} AS {quote(alias)}')
        filters = plan.get('filters', [])
        if not isinstance(filters,list) or len(filters) > 30:
            raise QueryRejected('At most 30 AND filters are supported')
        conditions = []
        for spec in filters:
            if not isinstance(spec,dict) or set(spec) - {'column','operator','value'}:
                raise QueryRejected('Invalid filter')
            expression, selected, _ = column(spec.get('column'))
            operator, value = spec.get('operator'), spec.get('value')
            if not isinstance(operator,str):
                raise QueryRejected('Filter operator must be a string')
            def scalar(item):
                if item is None or type(item) not in (str,int,float,bool) or isinstance(item,float) and not math.isfinite(item):
                    raise QueryRejected('Filter values must be finite JSON scalars; use is_null for nulls')
                if isinstance(item,str) and len(item) > 1000:
                    raise QueryRejected('Filter value is too long')
                if selected.data_type in {'integer','number'} and type(item) not in (int,float):
                    raise QueryRejected('Numeric filters need numeric values')
                if selected.data_type == 'boolean' and type(item) is not bool:
                    raise QueryRejected('Boolean filters need boolean values')
                if selected.data_type == 'date':
                    try:
                        return date.fromisoformat(item)
                    except (TypeError,ValueError):
                        raise QueryRejected('Date filter must be YYYY-MM-DD') from None
                if selected.data_type == 'datetime':
                    try:
                        return datetime.fromisoformat(item)
                    except (TypeError,ValueError):
                        raise QueryRejected('Datetime filter must be ISO formatted') from None
                return item
            comparisons = {'eq':'=','ne':'<>','gt':'>','gte':'>=','lt':'<','lte':'<='}
            if operator in {'is_null','not_null'}:
                conditions.append(f'{expression} IS {"NOT " if operator == "not_null" else ""}NULL')
            elif operator in comparisons:
                conditions.append(f'{expression} {comparisons[operator]} ?')
                parameters.append(scalar(value))
            elif operator == 'in':
                if not isinstance(value,list) or not 1 <= len(value) <= 100:
                    raise QueryRejected('IN needs 1 to 100 scalar values')
                conditions.append(f'{expression} IN ({",".join("?" for _ in value)})')
                parameters.extend(scalar(v) for v in value)
            elif operator == 'contains' and selected.data_type == 'string' and isinstance(value,str):
                conditions.append(f'contains({expression}, ?)')
                parameters.append(scalar(value))
            else:
                raise QueryRejected('Unsupported filter operator')
        order = []
        order_specs = plan.get('order_by', [])
        if not isinstance(order_specs,list) or len(order_specs) > 10:
            raise QueryRejected('Invalid ordering')
        for spec in order_specs:
            if (not isinstance(spec,dict) or set(spec) - {'column','direction'}
                or not isinstance(spec.get('column'),str) or spec.get('column') not in output
                or not isinstance(spec.get('direction','asc'),str) or spec.get('direction','asc') not in {'asc','desc'}):
                raise QueryRejected('Order by a selected alias using asc/desc')
            order.append(f'{quote(spec["column"])} {spec.get("direction","asc").upper()} NULLS LAST')
        limit = plan.get('limit',100)
        if type(limit) is not int or not 1 <= limit <= 500:
            raise QueryRejected('Result limit must be from 1 to 500')
        chart = plan.get('chart')
        if chart is not None:
            if (not isinstance(chart,dict) or set(chart) - {'type','x','y','title'}
                or not isinstance(chart.get('type'),str) or chart.get('type') not in {'bar','line'}):
                raise QueryRejected('Only declarative bar/line charts are supported')
            if (not isinstance(chart.get('x'),str) or chart.get('x') not in output
                or not isinstance(chart.get('y'),list) or not 1 <= len(chart['y']) <= 3
                or any(not isinstance(key,str) for key in chart['y']) or len(set(chart['y'])) != len(chart['y'])):
                raise QueryRejected('Chart axes must refer to selected aliases')
            if any(output.get(key) not in {'integer','number'} for key in chart['y']):
                raise QueryRejected('Chart Y axes require numeric results')
            if len({metadata[key]['percentage'] for key in chart['y']}) > 1:
                raise QueryRejected('Percentage and non-percentage series need separate charts')
            if not isinstance(chart.get('title',''),str) or len(chart.get('title','')) > 200:
                raise QueryRejected('Invalid chart title')
            chart = {key:chart[key] for key in ('type','x','y','title') if key in chart}
            if chart['type'] == 'line' and not order:
                order.append(f'{quote(chart["x"])} ASC NULLS LAST')
        if not aggregated:
            for i in range(len(bindings)):
                expressions += [f'{quote(f"d{i}")}."__source_row" AS {quote(f"__row_{i}")}',
                                f'{quote(f"d{i}")}."__dataset_id" AS {quote(f"__dataset_{i}")}']
        sql = f'SELECT {", ".join(expressions)} FROM "d0" ' + ' '.join(joins)
        if conditions:
            sql += ' WHERE ' + ' AND '.join(conditions)
        if aggregated and dimensions:
            sql += ' GROUP BY ' + ', '.join(dimensions)
        if order:
            sql += ' ORDER BY ' + ', '.join(order)
        sql += f' LIMIT {limit+1}'
        all_datasets = (*base_group, *datasets[1:])
        if len({d.id for d in all_datasets}) != len(all_datasets):
            raise QueryRejected('A dataset cannot be both unioned and joined')
        return CompiledPlan(sql, tuple(parameters), tuple(all_datasets), tuple(checks), limit, aggregated, chart,tuple(bindings),metadata)
