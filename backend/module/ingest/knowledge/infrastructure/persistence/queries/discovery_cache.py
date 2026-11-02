"""Memoize repeated vector reads only for the lifetime of one discovery call."""
from contextlib import contextmanager
from contextvars import ContextVar


_candidates = ContextVar('knowledge_discovery_vector_candidates', default=None)


@contextmanager
def vector_candidate_scope():
    token = _candidates.set({})
    try:
        yield
    finally:
        _candidates.reset(token)


async def vector_candidates(key, load):
    cache = _candidates.get()
    if cache is not None and key in cache:
        return cache[key]
    rows = tuple(await load())
    if cache is not None:
        cache[key] = rows
    return rows
