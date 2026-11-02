from module.ingest.chunking.application.services.chunk_budget import ChunkBudget
from module.ingest.chunking.application.services.smart_chunker import SmartChunker
from .streaming_chunking_engine import StreamingChunkingEngine


class SmartChunkingEngine(StreamingChunkingEngine):
    """Section-aware chunks sized for the embedding model (cl100k_base for text-embedding-3)."""

    def __init__(self, *, target_tokens=2000, max_chunk_tokens=4000, reserve_tokens=64,
                 include_heading_context=True, reader=None, counter=None):
        if counter is None:
            from .token_counter import TiktokenCounter
            counter = TiktokenCounter('cl100k_base')
        super().__init__(max_chunk_tokens=max_chunk_tokens, reserve_tokens=reserve_tokens,
                         reader=reader, counter=counter)
        self.planner = SmartChunker(ChunkBudget(max_chunk_tokens, reserve_tokens, counter),
                                    target_tokens=target_tokens,
                                    include_heading_context=include_heading_context)
