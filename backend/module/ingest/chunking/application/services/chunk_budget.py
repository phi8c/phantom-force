import json
import re
from module.ingest.chunking.domain.contracts.token_counter import TokenCounter


class Utf8UpperBoundCounter:
    """Offline upper bound for byte-based tokenizers; deliberately conservative."""
    def count(self, text):
        return len(text.encode('utf-8'))


class ChunkBudget:
    def __init__(self, max_tokens=800, reserve_tokens=64, counter: TokenCounter | None = None):
        if max_tokens <= reserve_tokens or reserve_tokens < 0:
            raise ValueError('Chunk budget must exceed its nonnegative context reserve')
        self.max_tokens = max_tokens
        self.reserve_tokens = reserve_tokens
        self.counter = counter if counter is not None else Utf8UpperBoundCounter()

    def count(self, content, metadata):
        # Same content/metadata JSON envelope sent to classification; model-wide
        # system prompts/document context are accounted for by a separate reserve.
        return self.counter.count(json.dumps({'content': content, 'metadata': metadata}, ensure_ascii=False))

    def fits(self, content, metadata):
        return self.count(content, metadata) + self.reserve_tokens <= self.max_tokens


def fitting_prefix(text, candidate):
    """Largest fitting prefix, preferring a nearby paragraph/sentence boundary."""
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if candidate(text[:middle]):
            low = middle
        else:
            high = middle - 1
    if low == 0:
        raise ValueError('Chunk budget is too small for source provenance and one character')
    if low < len(text):
        boundaries = [match.end() for match in re.finditer(r'\n+|[.!?。！？]\s+', text[:low])]
        if boundaries and boundaries[-1] >= low // 2:
            return boundaries[-1]
    return low


def provenance(block, heading_path):
    # Derived context is bounded; authoritative heading text is still emitted.
    path = [title[:80] for title in heading_path[-3:]]
    return {
        'schema_version': 2,
        'source_block_ids': [block.id],
        'section_ids': [block.section_id] if block.section_id else [],
        'part_ids': [block.source.part_id] if block.source.part_id else [],
        'heading_path': path,
    }
