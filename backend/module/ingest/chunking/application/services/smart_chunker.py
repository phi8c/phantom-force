"""Heading-aware chunking sized for an embedding model.

Sections are measured once, then packed top-down: a section that fits
`target_tokens` stays whole; a larger one is split along its children and every
resulting chunk keeps the parent's heading as context. Only a leaf above the
hard cap is cut, at block boundaries, into balanced pieces. Documents without
headings are packed by paragraph under the document title.

Tokens are counted on chunk content only because the embedding step sends
`chunk.content` alone, so the heading context is written into the content.
"""
import math
from collections.abc import Iterator
from dataclasses import dataclass, field, replace

from shared.ingestion.document import BlockKind
from module.ingest.chunking.domain.contracts.chunking_engine import Chunk
from .chunk_budget import ChunkBudget, fitting_prefix, provenance
from .table_chunker import TableChunker

SEPARATOR = '\n\n'
BREADCRUMB = ' › '
_ORPHAN = -1
_MIN_ROOM = 24  # tokens; below this a partly filled chunk is closed instead of squeezing text in


@dataclass(slots=True)
class _Node:
    id: str
    title: str
    parent_id: str | None
    children: list = field(default_factory=list)
    own: int = 0
    total: int = 0


class SmartChunker:
    """Deterministic planning over the section tree; reader and coverage stay injected ports."""

    def __init__(self, budget: ChunkBudget, *, target_tokens: int = 2000, include_heading_context: bool = True):
        self.cap = budget.max_tokens - budget.reserve_tokens
        if not 0 < target_tokens <= self.cap:
            raise ValueError('target_tokens must be positive and not exceed the chunk budget')
        self.budget = budget
        self.target = target_tokens
        self.stub = max(_MIN_ROOM, target_tokens // 10)  # smaller than this never stands alone
        self.context = include_heading_context
        self.tables = TableChunker(budget)
        self._count = budget.counter.count
        self._separator = self._count(SEPARATOR)

    def chunks(self, source, context_for=None) -> Iterator[Chunk]:
        """`context_for` (LLM review hints) is accepted for engine compatibility and ignored."""
        nodes, roots, sizes = self._measure(source)
        unit_of = self._plan(nodes, roots)
        title = getattr(source, 'title', None)
        chains = {}
        sequence = 0
        pending, unit = [], _ORPHAN

        def chain(section_id):
            if section_id not in chains:
                node = nodes[section_id]
                chains[section_id] = (*(chain(node.parent_id) if node.parent_id else ()), node)
            return chains[section_id]

        def flush():
            nonlocal sequence
            for group in self._groups(pending, unit == _ORPHAN, chain, title):
                yield replace(self._emit(source, group, chain, title), index=sequence)
                sequence += 1

        for block in source.blocks():
            block_unit = unit_of.get(block.section_id, _ORPHAN)
            if pending and (block_unit != unit or block.kind == BlockKind.TABLE):
                yield from flush()
                pending = []
            unit = block_unit
            if block.kind == BlockKind.TABLE:
                path = tuple(node.title for node in chain(block.section_id)) if block.section_id else ()
                for chunk in self.tables.chunks(block, source.table(block.table_id), path, source):
                    yield replace(chunk, index=sequence)
                    sequence += 1
            else:
                pending.append((block, 0, len(block.text), sizes[block.id]))
        if pending:
            yield from flush()
        source.finish_coverage()
        if not sequence:
            raise ValueError('Chunking produced zero chunks')

    # -- planning -----------------------------------------------------------------

    def _measure(self, source):
        nodes = {row[0]: _Node(row[0], row[3], row[1]) for row in getattr(source, 'sections', lambda: ())()}
        roots = []
        for node in nodes.values():
            (nodes[node.parent_id].children if node.parent_id else roots).append(node)
        sizes = {}
        for block in source.blocks():
            if block.kind != BlockKind.TABLE:  # tables are chunked separately
                sizes[block.id] = self._count(block.text)
                if block.section_id:
                    nodes[block.section_id].own += sizes[block.id]
        for root in roots:
            self._total(root)
        return nodes, roots, sizes

    def _total(self, node):
        node.total = node.own + sum(self._total(child) for child in node.children)
        return node.total

    def _fits(self, node):
        return node.total <= self.target or (not node.children and node.total <= self.cap)

    def _plan(self, nodes, roots):
        # A stub (a bare parent heading, a one-line intro) never becomes a chunk of its own: it rides
        # along with the next unit, which keeps it as heading context anyway.
        unit_of, count, carried = {}, [0], []

        def assign(ids):
            for section_id in (*carried, *ids):
                unit_of[section_id] = count[0]
            carried.clear()
            count[0] += 1

        def subtree(node):
            yield node.id
            for child in node.children:
                yield from subtree(child)

        def pack(parts):
            """parts: (ids, tokens, node to descend into | None, standalone)."""
            group, size = [], 0
            for ids, tokens, descend, alone in parts:
                if descend is not None or alone:
                    if group:
                        (carried.extend if size < self.stub else assign)(group)
                        group, size = [], 0
                    if descend is not None:
                        pack(self._parts(descend, subtree))
                    else:
                        assign(ids)
                elif group and size + tokens > self.target:
                    (carried.extend if size < self.stub else assign)(group)
                    group, size = list(ids), tokens
                else:
                    group.extend(ids)
                    size += tokens
            if group:
                assign(group)

        pack(self._siblings(roots, subtree))
        return unit_of

    def _siblings(self, siblings, subtree):
        return [(list(subtree(node)), node.total, None if self._fits(node) else node, False) for node in siblings]

    def _parts(self, node, subtree):
        # The heading and intro text come first in reading order, then each child section.
        return [([node.id], node.own, None, node.own > self.target), *self._siblings(node.children, subtree)]

    # -- emission -----------------------------------------------------------------

    def _prefix(self, lca, first, title):
        titles = [node.title for node in lca]
        if titles and first.kind == BlockKind.HEADING and first.section_id == lca[-1].id:
            titles.pop()  # the section's own heading is already the first line of the content
        if not titles and not lca and title:
            titles = [title]
        return BREADCRUMB.join(titles) if self.context and titles else ''

    def _groups(self, entries, orphan, chain, title):
        """Split one unit's blocks into chunk-sized groups."""
        first = entries[0][0]
        prefix_cost = self._count(self._prefix(chain(first.section_id) if first.section_id else (), first, title)
                                  + SEPARATOR)
        total = sum(entry[3] for entry in entries) + self._separator * (len(entries) - 1)
        if total + prefix_cost <= (self.target if orphan else self.cap):
            return [entries]
        pieces = max(1, math.ceil(total / self.target))
        limit = max(_MIN_ROOM, min(self.cap, math.ceil(total / pieces)) - prefix_cost)
        return self._balance(entries, limit, self.cap - prefix_cost)

    def _balance(self, entries, limit, cap):
        atoms, atom = [], []
        for entry in entries:  # a heading never ends a chunk: it travels with the block after it
            atom.append(entry)
            if entry[0].kind != BlockKind.HEADING:
                atoms.append(atom)
                atom = []
        if atom:
            atoms.append(atom)
        sized = [(atom, sum(entry[3] for entry in atom) + self._separator * (len(atom) - 1)) for atom in atoms]
        groups = self._fill(sized, limit, cap)
        if len(groups) > 1 and all(size <= cap for _, size in sized):
            # Whole blocks cannot be split, so even out the pieces: smallest limit that keeps the same count.
            low, high = math.ceil(sum(size for _, size in sized) / len(groups)), limit
            while low < high:
                middle = (low + high) // 2
                if len(self._fill(sized, middle, cap)) <= len(groups):
                    high = middle
                else:
                    low = middle + 1
            groups = self._fill(sized, high, cap)
        return groups

    def _fill(self, sized, limit, cap):
        groups, group, used = [], [], 0
        for atom, size in sized:
            cost = size + (self._separator if group else 0)
            if group and used + cost > limit:
                groups.append(group)
                group, used, cost = [], 0, size
            if size <= cap:
                group.extend(atom)
                used += cost
                continue
            for entry in atom:  # one block larger than any chunk: cut it at sentence/paragraph edges
                for piece in self._cut(entry, limit if not group else max(limit - used, 0), limit):
                    if piece is None:
                        if group:
                            groups.append(group)
                        group, used = [], 0
                    else:
                        group.append(piece)
                        used += piece[3] + (self._separator if len(group) > 1 else 0)
        if group:
            groups.append(group)
        return groups

    def _cut(self, entry, room, limit):
        """Yield pieces of one oversized block; None marks "close the current chunk"."""
        block, start, end, tokens = entry
        if tokens <= limit and tokens <= room:
            yield entry
            return
        position = start
        while position < end:
            if room < _MIN_ROOM:
                yield None
                room = limit
            size = fitting_prefix(block.text[position:end], lambda value: self._count(value) <= room)
            piece = (block, position, position + size, self._count(block.text[position:position + size]))
            position += size
            yield piece
            if position < end:
                yield None
                room = limit
            else:
                room -= piece[3]

    def _emit(self, source, entries, chain, title):
        sections = [chain(entry[0].section_id) if entry[0].section_id else () for entry in entries]
        lca = sections[0]
        for other in sections[1:]:
            shared = 0
            while shared < min(len(lca), len(other)) and lca[shared].id == other[shared].id:
                shared += 1
            lca = lca[:shared]
        prefix = self._prefix(lca, entries[0][0], title)
        offset = len(prefix) + len(SEPARATOR) if prefix else 0
        pieces, spans, block_ids, section_ids, part_ids = [], [], [], [], []
        for index, (block, start, end, _) in enumerate(entries):
            if index:
                offset += len(SEPARATOR)
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
        body = SEPARATOR.join(pieces)
        content = f'{prefix}{SEPARATOR}{body}' if prefix else body
        path = [node.title for node in lca]
        metadata = {**provenance(entries[-1][0], path),
                    'source_block_ids': list(dict.fromkeys(block_ids)),
                    'section_ids': list(dict.fromkeys(section_ids)),
                    'part_ids': list(dict.fromkeys(part_ids)), 'text_spans': spans}
        if prefix:
            metadata['context_prefix'] = prefix
        for span in spans:
            source.record_text(span['block_id'], span['start'], span['end'],
                               content[span['content_start']:span['content_end']])
        return Chunk(-1, path[-1] if path else None, content, metadata)
