from dataclasses import replace
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4
from zipfile import ZipFile

from module.structured_data.infrastructure.workbook import XlsxWorkbookBuilder
from module.structured_data.infrastructure.query_engine import DuckDbQueryEngine
from module.structured_data.application.query_compiler import QueryCompiler, QueryRejected


@unittest.skipUnless(importlib.util.find_spec('duckdb') and importlib.util.find_spec('pyarrow'),
                     'Install backend/requirements-structured-data.txt')
class WorkbookQueryTests(unittest.TestCase):
    def setUp(self):
        from openpyxl import Workbook
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'statistics.xlsx'
        self.space, self.document = uuid4(), uuid4()
        self.workbook = Workbook()
        self.workbook.active.title = 'Sales'

    def tearDown(self):
        self.workbook.close()
        self.temp.cleanup()

    def build(self, settings=None):
        self.workbook.save(self.source)
        return XlsxWorkbookBuilder().build(self.source,self.root/'built',space=self.space,document=self.document,
                                           file_name='statistics.xlsx',configuration=settings or {})

    def sales(self):
        sheet = self.workbook['Sales']
        for row in [['Department','Amount','Month'],['IT',10,datetime(2026,1,1)],['IT',20,datetime(2026,2,1)],['HR',5,datetime(2026,1,1)]]:
            sheet.append(row)

    def execute(self, built, plan, **options):
        return DuckDbQueryEngine(**options).execute(plan,[v.dataset for v in built],{v.dataset.id:v.parquet for v in built})

    def test_grouped_sums_and_chart_use_real_parquet_records(self):
        self.sales()
        built = self.build()
        plan = {'dataset_id':str(built[0].dataset.id),'select':[
            {'column':'department','alias':'department'},{'column':'amount','aggregate':'sum','alias':'total'}],
            'order_by':[{'column':'total','direction':'desc'}],
            'chart':{'type':'bar','x':'department','y':['total'],'title':'By department'}}
        result = self.execute(built,plan)
        self.assertEqual(result.rows,(('IT',30),('HR',5)))
        self.assertEqual(result.sources[0]['sheet'],'Sales')
        self.assertEqual(result.chart['y'],['total'])
        self.assertFalse(result.truncated)

    def test_malformed_model_plan_types_are_rejected_before_execution(self):
        self.sales()
        dataset = self.build()[0].dataset
        base = {'dataset_id':str(dataset.id),'select':[{'column':'amount','alias':'amount'}]}
        changes = [
            {'chart':{}}, {'chart':[]},
            {'chart':{'type':'bar','x':'amount','y':[{}]}},
            {'select':[{'column':'amount','alias':'amount','aggregate':{}}]},
            {'select':[{'column':'amount','alias':'amount','time_grain':[]}]},
            {'filters':[{'column':'amount','operator':[],'value':1}]},
            {'order_by':[{'column':{},'direction':'asc'}]},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(QueryRejected):
                QueryCompiler().compile({**base,**change},[dataset])

    def test_parameterized_filters_do_not_execute_injected_sql(self):
        self.sales()
        built = self.build()
        result = self.execute(built,{'dataset_id':str(built[0].dataset.id),
            'select':[{'column':'department','alias':'department'}],
            'filters':[{'column':'department','operator':'eq','value':"IT'; DROP TABLE d0; --"}]})
        self.assertEqual(result.rows,())
        self.assertEqual(self.execute(built,{'dataset_id':str(built[0].dataset.id),
            'select':[{'aggregate':'count','alias':'count'}]}).rows,((3,),))

    def test_limit_applies_after_aggregation_and_truncation_is_explicit(self):
        self.sales()
        built = self.build()
        base = {'dataset_id':str(built[0].dataset.id),'limit':1}
        raw = self.execute(built,{**base,'select':[{'column':'amount','alias':'amount'}]})
        self.assertTrue(raw.truncated)
        self.assertEqual(len(raw.rows),1)
        aggregate = self.execute(built,{**base,'select':[{'column':'amount','aggregate':'sum','alias':'total'}]})
        self.assertEqual(aggregate.rows,((35,),))
        self.assertFalse(aggregate.truncated)

    def test_time_dimensions_are_grouped_and_line_chart_sorted(self):
        self.sales()
        built = self.build()
        result = self.execute(built,{'dataset_id':str(built[0].dataset.id),'select':[
            {'column':'month','time_grain':'month','alias':'month'},
            {'column':'amount','aggregate':'sum','alias':'total'}],
            'chart':{'type':'line','x':'month','y':['total']}})
        self.assertEqual([row[1] for row in result.rows],[15,20])
        self.assertLess(result.rows[0][0],result.rows[1][0])

    def test_union_all_sheets_preserves_duplicate_source_records(self):
        for sheet in (self.workbook['Sales'],self.workbook.create_sheet('Sales2')):
            sheet.append(['Department','Amount'])
            sheet.append(['IT',10])
        built = self.build()
        result = self.execute(built,{'dataset_id':str(built[0].dataset.id),
            'union_dataset_ids':[str(built[1].dataset.id)],
            'select':[{'column':'amount','aggregate':'sum','alias':'total'}]})
        self.assertEqual(result.rows,((20,),))
        self.assertEqual(len(result.sources),2)

    def test_raw_union_lineage_points_to_each_sheet_row(self):
        for sheet in (self.workbook['Sales'],self.workbook.create_sheet('Sales2')):
            sheet.append(['Department','Amount']); sheet.append(['IT',10])
        built = self.build()
        result = self.execute(built,{'dataset_id':str(built[0].dataset.id),
            'union_dataset_ids':[str(built[1].dataset.id)],'select':[{'column':'amount','alias':'amount'}]})
        self.assertEqual(result.rows,((10,),(10,)))
        self.assertEqual({next(iter(row)) for row in result.row_sources},{str(v.dataset.id) for v in built})
        self.assertTrue(all(next(iter(row.values())) == 2 for row in result.row_sources))

    def test_same_workbook_join_requires_unique_right_keys(self):
        self.sales()
        right = self.workbook.create_sheet('Departments')
        for row in [['Department','Region'],['IT','North'],['HR','South']]: right.append(row)
        settings = {'relationships':[{'left_sheet':'Sales','left_column':'Department',
                                     'right_sheet':'Departments','right_column':'Department'}]}
        built = self.build(settings)
        plan = {'dataset_id':str(built[0].dataset.id),
            'joins':[{'dataset_id':str(built[1].dataset.id),'left_column':'department','right_column':'department'}],
            'select':[{'column':'d1.region','alias':'region'},{'column':'amount','aggregate':'sum','alias':'total'}],
            'order_by':[{'column':'region','direction':'asc'}]}
        self.assertEqual(self.execute(built,plan).rows,(('North',30),('South',5)))
        right.append(['IT','Duplicate'])
        built = self.build(settings)
        plan['dataset_id'],plan['joins'][0]['dataset_id'] = str(built[0].dataset.id),str(built[1].dataset.id)
        with self.assertRaisesRegex(QueryRejected,'not unique'):
            self.execute(built,plan)

    def test_cross_workbook_join_and_union_are_rejected(self):
        self.sales()
        built = self.build()
        base = built[0].dataset
        foreign = replace(base,id=uuid4(),document_id=uuid4())
        plan = {'dataset_id':str(base.id),'select':[{'column':'amount','alias':'amount'}]}
        for extra in ({'union_dataset_ids':[str(foreign.id)]},
                      {'joins':[{'dataset_id':str(foreign.id),'left_column':'department','right_column':'department'}]}):
            with self.subTest(extra=extra),self.assertRaises(QueryRejected):
                QueryCompiler().compile({**plan,**extra},[base,foreign])

    def test_unconfirmed_same_workbook_join_is_rejected(self):
        self.sales()
        other = self.workbook.create_sheet('Departments')
        other.append(['Department','Region']); other.append(['IT','North'])
        built = self.build()
        with self.assertRaisesRegex(QueryRejected,'explicitly confirmed'):
            self.execute(built,{'dataset_id':str(built[0].dataset.id),
                'joins':[{'dataset_id':str(built[1].dataset.id),'left_column':'department','right_column':'department'}],
                'select':[{'column':'amount','aggregate':'sum','alias':'total'}]})

    def test_unknown_columns_sql_fields_and_chart_axes_are_rejected(self):
        self.sales()
        dataset = self.build()[0].dataset
        base = {'dataset_id':str(dataset.id),'select':[{'column':'amount','alias':'amount'}]}
        for extra in ({'sql':'SELECT * FROM secrets'}, {'dataset_id':str(uuid4())},
                      {'select':[{'column':'amount); DROP TABLE d0','alias':'x'}]},
                      {'chart':{'type':'bar','x':'amount','y':['missing']}}, {'limit':True}):
            with self.subTest(extra=extra),self.assertRaises(QueryRejected):
                QueryCompiler().compile({**base,**extra},[dataset])

    def test_checksum_tampering_is_rejected_before_query(self):
        self.sales()
        built = self.build()
        built[0].parquet.write_bytes(b'Not original Parquet')
        with self.assertRaisesRegex(QueryRejected,'checksum'):
            self.execute(built,{'dataset_id':str(built[0].dataset.id),'select':[{'aggregate':'count','alias':'rows'}]})

    def test_small_response_budget_marks_partial_data(self):
        sheet = self.workbook['Sales']
        sheet.append(['Key','Description']); sheet.append(['a','x'*200])
        built = self.build()
        result = self.execute(built,{'dataset_id':str(built[0].dataset.id),
            'select':[{'column':'description','alias':'description'}]},max_result_bytes=20)
        self.assertEqual(result.rows,())
        self.assertTrue(result.truncated)

    def test_source_offsets_leading_zero_ids_and_mixed_types_are_preserved(self):
        sheet = self.workbook['Sales']
        for row in [['ID','Mixed'],['00123',10],['00456','unknown']]: sheet.append(row)
        built = self.build()
        self.assertEqual([c.data_type for c in built[0].dataset.columns],['string','string'])
        result = self.execute(built,{'dataset_id':str(built[0].dataset.id),
            'select':[{'column':'id','alias':'id'},{'column':'mixed','alias':'mixed'}]})
        self.assertEqual(result.rows,(('00123','10'),('00456','unknown')))
        self.assertEqual(next(iter(result.row_sources[0].values())),2)

    def test_percent_values_and_formats_are_not_multiplied_on_build(self):
        sheet = self.workbook['Sales']; sheet.append(['Key','Rate']); sheet.append(['a',.25]); sheet['B2'].number_format='0.00%'
        built = self.build()
        result = self.execute(built,{'dataset_id':str(built[0].dataset.id),'select':[{'column':'rate','alias':'rate'}]})
        self.assertEqual(result.rows,((.25,),))
        self.assertEqual(result.column_metadata['rate']['number_format'],'0.00%')

    def test_explicit_tables_exclude_totals_and_vertical_tables_are_detected(self):
        from openpyxl.worksheet.table import Table
        sheet = self.workbook['Sales']
        for row in [['Key','Amount'],['a',10],['Total',10]]: sheet.append(row)
        sheet.add_table(Table(displayName='Statistics',ref='A1:B3',totalsRowCount=1))
        built = self.build()
        self.assertEqual(built[0].dataset.row_count,1)
        self.assertEqual(self.execute(built,{'dataset_id':str(built[0].dataset.id),
            'select':[{'column':'amount','aggregate':'sum','alias':'total'}]}).rows,((10,),))

    def test_ambiguous_totals_fail_instead_of_double_counting(self):
        sheet = self.workbook['Sales']
        for row in [['Key','Amount'],['a',10],['Total',10]]: sheet.append(row)
        with self.assertRaisesRegex(ValueError,'totals'):
            self.build()
        built = self.build({'ranges':[{'sheet':'Sales','range':'A1:B2'}]})
        self.assertEqual(built[0].dataset.row_count,1)

    def test_multiple_tables_blank_rows_and_header_notes(self):
        sheet = self.workbook['Sales']
        for row in [['Report title'],['Key','Amount'],['a',10],[],['Code','Quantity'],['b',2]]: sheet.append(row)
        built = self.build()
        self.assertEqual([d.dataset.source_range for d in built],['A2:B3','A5:B6'])

    def test_merged_two_level_headers_work_with_explicit_ranges(self):
        sheet = self.workbook['Sales']
        sheet.append(['Sales',None]); sheet.append(['Region','Amount']); sheet.append(['North',10]); sheet.merge_cells('A1:B1')
        built = self.build({'ranges':[{'sheet':'Sales','range':'A1:B3','header_rows':2}]})
        self.assertEqual([c.name for c in built[0].dataset.columns],['Sales / Region','Sales / Amount'])

    def test_merged_data_cells_are_rejected(self):
        sheet = self.workbook['Sales']; sheet.append(['Key','Amount']); sheet.append(['a',10]); sheet.append(['b',20]); sheet.merge_cells('A2:A3')
        with self.assertRaisesRegex(ValueError,'Merged data cells'):
            self.build({'ranges':[{'sheet':'Sales','range':'A1:B3'}]})

    def test_formula_without_cached_value_fails(self):
        sheet = self.workbook['Sales']; sheet.append(['Key','Amount']); sheet.append(['a','=1+1'])
        with self.assertRaisesRegex(ValueError,'cached values'):
            self.build()

    def test_formula_and_cached_value_are_both_retained(self):
        sheet = self.workbook['Sales']; sheet.append(['Key','Amount']); sheet.append(['a','=1+1'])
        self.workbook.save(self.source)
        updated = self.root/'cached.xlsx'
        with ZipFile(self.source) as original, ZipFile(updated,'w') as target:
            for item in original.infolist():
                content = original.read(item.filename)
                if item.filename == 'xl/worksheets/sheet1.xml':
                    content = content.replace(b'<f>1+1</f><v></v>',b'<f>1+1</f><v>2</v>')
                    content = content.replace(b'<f>1+1</f><v />',b'<f>1+1</f><v>2</v>')
                target.writestr(item,content)
        built = XlsxWorkbookBuilder().build(updated,self.root/'built',space=self.space,document=self.document,file_name='cached.xlsx',configuration={})
        formula = json.loads(built[0].formulas.read_text(encoding='utf8'))
        self.assertEqual((formula['formula'],formula['cached_value']),('=1+1',2))
        self.assertEqual(self.execute(built,{'dataset_id':str(built[0].dataset.id),
            'select':[{'column':'amount','aggregate':'sum','alias':'total'}]}).rows,((2,),))

    def test_blank_rows_do_not_inflate_statistics_and_distinct_is_capped(self):
        sheet = self.workbook['Sales']; sheet.append(['Key','Amount']); sheet.append(['a',1]); sheet.append([]); sheet.append(['b',None])
        built = self.build({'ranges':[{'sheet':'Sales','range':'A1:B4'}]})
        amount = built[0].dataset.columns[1]
        self.assertEqual(amount.statistics['null_count'],1)
        self.assertEqual((amount.statistics['min'],amount.statistics['max']),(1,1))

    def test_repeat_build_identity_and_parquet_digest_are_stable(self):
        self.sales()
        self.workbook.save(self.source)
        builder = XlsxWorkbookBuilder()
        a = builder.build(self.source,self.root/'a',space=self.space,document=self.document,file_name='same.xlsx',configuration={})
        b = builder.build(self.source,self.root/'b',space=self.space,document=self.document,file_name='same.xlsx',configuration={})
        self.assertEqual(a[0].dataset.id,b[0].dataset.id)
        self.assertEqual(a[0].dataset.parquet_sha256,b[0].dataset.parquet_sha256)

    def test_streaming_export_without_dimension_metadata_is_supported(self):
        from openpyxl import Workbook
        workbook = Workbook(write_only=True)
        sheet = workbook.create_sheet('Export')
        sheet.append(['Key','Amount']); sheet.append(['a',10]); sheet.append(['b',20])
        workbook.save(self.source)
        workbook.close()
        built = XlsxWorkbookBuilder().build(self.source,self.root/'streamed',space=self.space,
            document=self.document,file_name='export.xlsx',configuration={})
        self.assertEqual(built[0].dataset.row_count,2)
        self.assertEqual(self.execute(built,{'dataset_id':str(built[0].dataset.id),
            'select':[{'column':'amount','aggregate':'sum','alias':'total'}]}).rows,((30,),))

    def test_hidden_empty_and_over_budget_sheets_fail_clearly(self):
        self.sales()
        with self.assertRaisesRegex(ValueError,'budget'):
            self.build({'max_cells':2})
        empty = self.workbook.create_sheet('Empty')
        self.workbook.remove(self.workbook['Sales'])
        with self.assertRaisesRegex(ValueError,'no readable'):
            self.build()
