"""Incremental root-object reader, retaining at most one selected array item.

Uses the standard JSON decoder for values and validates skipped containers too.
No complete document/array is loaded. An individual table is still one item.
"""
import json


class JsonObjectItems:
    def __init__(self, stream, *, max_item_chars=64 * 1024 * 1024, arrays=None, fields=None):
        self.stream = stream
        self.buffer = ''
        self.position = 0
        self.eof = False
        self.limit = max_item_chars
        self.decoder = json.JSONDecoder()
        self.arrays = {'blocks', 'tables', 'sections'} if arrays is None else set(arrays)
        self.fields = {'schema_version', 'document_id'} if fields is None else set(fields)

    def _fill(self):
        self.buffer = self.buffer[self.position:]
        self.position = 0
        data = self.stream.read(64 * 1024)
        self.eof = not data
        self.buffer += data

    def peek(self):
        while self.position >= len(self.buffer) and not self.eof:
            self._fill()
        return self.buffer[self.position] if self.position < len(self.buffer) else ''

    def whitespace(self):
        while self.peek() and self.peek() in ' \t\r\n':
            self.position += 1

    def expect(self, value):
        self.whitespace()
        if self.peek() != value:
            raise ValueError(f'Invalid JSON: expected {value!r}')
        self.position += 1

    def value(self):
        self.whitespace()
        while True:
            try:
                value, end = self.decoder.raw_decode(self.buffer, self.position)
                if end - self.position > self.limit:
                    raise ValueError('A JSON item exceeds the configured memory limit')
                # A number at a read boundary might not yet be complete.
                if type(value) in (int, float) and end == len(self.buffer) and not self.eof:
                    self._fill()
                    continue
                self.position = end
                return value
            except json.JSONDecodeError:
                if self.eof:
                    raise ValueError('Invalid or truncated JSON') from None
                if len(self.buffer) - self.position > self.limit:
                    raise ValueError('A JSON item exceeds the configured memory limit')
                self._fill()

    def skip(self, depth=0):
        if depth > 128:
            raise ValueError('JSON nesting exceeds supported depth')
        self.whitespace()
        marker = self.peek()
        if marker not in {'[', '{'}:
            self.value()
            return
        self.position += 1
        closing = ']' if marker == '[' else '}'
        self.whitespace()
        if self.peek() == closing:
            self.position += 1
            return
        while True:
            if marker == '{':
                if not isinstance(self.value(), str):
                    raise ValueError('JSON object keys must be strings')
                self.expect(':')
            self.skip(depth + 1)
            self.whitespace()
            if self.peek() == closing:
                self.position += 1
                return
            self.expect(',')

    def items(self):
        self.expect('{')
        seen = set()
        self.whitespace()
        if self.peek() == '}':
            self.position += 1
        else:
            while True:
                key = self.value()
                if not isinstance(key, str) or key in seen:
                    raise ValueError('Invalid or duplicate root JSON key')
                seen.add(key)
                self.expect(':')
                if key in self.arrays:
                    self.expect('[')
                    yield 'array', key, None
                    self.whitespace()
                    if self.peek() != ']':
                        while True:
                            yield 'item', key, self.value()
                            self.whitespace()
                            if self.peek() == ']':
                                break
                            self.expect(',')
                    self.expect(']')
                elif key in self.fields:
                    yield 'field', key, self.value()
                else:
                    self.skip()
                self.whitespace()
                if self.peek() == '}':
                    self.position += 1
                    break
                self.expect(',')
        self.whitespace()
        if self.peek():
            raise ValueError('Trailing data after extraction JSON')
