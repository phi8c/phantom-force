from dataclasses import replace
from collections.abc import Iterator

from shared.ingestion.document import BlockKind
from module.ingest.chunking.domain.contracts.chunking_engine import Chunk
from module.ingest.chunking.domain.contracts.document_reader import IndexedContent
from .chunk_budget import fitting_prefix, provenance
from .table_chunker import TableChunker


class BlockChunker:
    """Deterministic planning; reader and coverage storage are injected ports."""

    def __init__(self, budget, *, strategy='SECTION', level=2):
        if strategy not in {'SECTION', 'PARAGRAPH'} or level < 1:
            raise ValueError('Invalid chunking strategy/section level')
        self.budget = budget
        self.strategy = strategy
        self.level = level
        self.tables = TableChunker(budget)

    def chunks(self, source: IndexedContent, context_for=None) -> Iterator[Chunk]:
        pending = []
        group = None
        sequence = 0

        def candidate(entries):
            pieces, spans = [], []
            block_ids, section_ids, part_ids = [], [], []
            offset = 0
            for block, start, end, path in entries:
                if pieces:
                    offset += 2
                value = block.text[start:end]
                spans.append({'block_id': block.id, 'start': start, 'end': end,
                              'content_start': offset, 'content_end': offset + len(value)})
                pieces.append(value)
                offset += len(value)
                block_ids.append(block.id)
                if block.section_id:
                    section_ids.append(block.section_id)
                if block.source.part_id:
                    part_ids.append(block.source.part_id)
            base = provenance(entries[-1][0], entries[-1][3])
            metadata = {**base, 'source_block_ids': list(dict.fromkeys(block_ids)),
                        'section_ids': list(dict.fromkeys(section_ids)), 'part_ids': list(dict.fromkeys(part_ids)),
                        'text_spans': spans}
            return '\n\n'.join(pieces), metadata

        def flush():
            content, metadata = candidate(pending)
            for span in metadata['text_spans']:
                source.record_text(span['block_id'], span['start'], span['end'],
                                   content[span['content_start']:span['content_end']])
            return Chunk(sequence, metadata['heading_path'][-1] if metadata['heading_path'] else None,
                         content, metadata)

        for block in source.blocks():
            key, path = (context_for(block) if context_for else
                         source.section_context(block.section_id, self.level if self.strategy == 'SECTION' else None))
            if pending and (key != group or block.kind == BlockKind.TABLE):
                yield flush()
                sequence += 1
                pending = []
            group = key
            if block.kind == BlockKind.TABLE:
                for chunk in self.tables.chunks(block, source.table(block.table_id), path, source):
                    yield replace(chunk, index=sequence)
                    sequence += 1
                continue
            position = 0
            while position < len(block.text):
                full = (block, position, len(block.text), path)
                if self.budget.fits(*candidate([*pending, full])):
                    pending.append(full)
                    break
                if pending:
                    yield flush()
                    sequence += 1
                    pending = []
                    continue
                size = fitting_prefix(block.text[position:], lambda value: self.budget.fits(
                    *candidate([(block, position, position + len(value), path)])))
                pending = [(block, position, position + size, path)]
                yield flush()
                sequence += 1
                pending = []
                position += size
        if pending:
            yield flush()
            sequence += 1
        source.finish_coverage()
        if not sequence:
            raise ValueError('Chunking produced zero chunks')
