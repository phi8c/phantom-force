"""Standard-library tests: do not import Docling, database or worker bootstrap."""
import json
import unittest
from dataclasses import asdict, replace

from shared.ingestion.document import (
    BlockKind, ContentBlock, DocumentSection, ExtractedDocumentV2,
    ExtractedTable, ExtractionMetadata, SourceLocation, StructureQuality, TableCell,
)
from shared.ingestion.parts import ExtractionManifest, ExtractionPart, PartStatus
from module.ingest.chunking.domain.contracts.structure_reviewer import (
    ReviewedGroup, ReviewWindow, StructureReview,
)


class DocumentContractTests(unittest.TestCase):
    def setUp(self):
        self.source = SourceLocation(native_block_index=0)
        self.block = ContentBlock("b1", 0, BlockKind.PARAGRAPH, self.source, text="Nội dung")
        self.document = ExtractedDocumentV2(
            "doc1", "Document", ExtractionMetadata("native", "1", StructureQuality.FLAT),
            (self.block,),
        )

    def test_flat_document_serializes_without_hierarchy(self):
        wire = json.loads(json.dumps(asdict(self.document), ensure_ascii=False))
        self.assertEqual(wire["schema_version"], 2)
        self.assertEqual(wire["sections"], [])
        self.assertEqual(wire["blocks"][0]["kind"], "paragraph")
        self.assertEqual(wire["blocks"][0]["text"], "Nội dung")

    def test_table_only_document_preserves_merged_cell(self):
        table = ExtractedTable("t1", 1, 2, (TableCell(0, 0, "Header", column_span=2),), self.source)
        block = ContentBlock("b2", 1, BlockKind.TABLE, self.source, table_id="t1")
        result = replace(self.document, blocks=(block,), tables=(table,))
        self.assertEqual(result.tables[0].cells[0].column_span, 2)

    def test_invalid_documents_fail_instead_of_silent_content_loss(self):
        cases = [
            {"blocks": ()},
            {"schema_version": 3},
            {"blocks": (self.block, self.block)},
            {"blocks": (replace(self.block, section_id="missing"),)},
            {"blocks": (ContentBlock("t", 0, BlockKind.TABLE, self.source, table_id="missing"),)},
            {"sections": (DocumentSection("s", "Title", 1, parent_id="missing"),)},
        ]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.document, **changes)

    def test_overlapping_and_out_of_bounds_cells_fail(self):
        for cells in [
            (TableCell(0, 0, "A", column_span=2), TableCell(0, 1, "B")),
            (TableCell(0, 0, "A", row_span=2),),
        ]:
            with self.subTest(cells=cells), self.assertRaises(ValueError):
                ExtractedTable("t1", 1, 2, cells, self.source)

    def test_reviewer_cannot_omit_duplicate_reorder_or_invent_blocks(self):
        second = replace(self.block, id="b2", order=1)
        window = ReviewWindow("doc1", "w1", (self.block, second))
        StructureReview("w1", (ReviewedGroup(None, ("b1", "b2")),)).validate_for(window)
        for ids in [("b1",), ("b1", "b1", "b2"), ("b2", "b1"), ("b1", "unknown")]:
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                StructureReview("w1", (ReviewedGroup(None, ids),)).validate_for(window)

    def test_review_overlap_is_context_only(self):
        second = replace(self.block, id="b2", order=1)
        window = ReviewWindow("doc1", "w2", (self.block, second), ("b1",))
        StructureReview("w2", (ReviewedGroup(None, ("b2",)),)).validate_for(window)

    def test_manifest_does_not_complete_when_a_part_is_pending(self):
        first = ExtractionPart("p1", 0, PartStatus.COMPLETED, 1, 20, "p1.json", "sha256")
        second = ExtractionPart("p2", 1, PartStatus.PENDING, 21, 40)
        manifest = ExtractionManifest("doc1", "source", "config", "page", (first, second))
        self.assertFalse(manifest.completed)
        with self.assertRaises(ValueError):
            replace(manifest, parts=(first, replace(second, source_start=22)))


if __name__ == "__main__":
    unittest.main()
