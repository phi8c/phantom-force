class TiktokenCounter:
    def __init__(self, encoding_name='o200k_base'):
        self.encoding_name = encoding_name
        self.encoding = None

    def count(self, text):
        if self.encoding is None:
            import tiktoken
            # Initialization is deferred to the off-loop iterator thread.
            self.encoding = tiktoken.get_encoding(self.encoding_name)
        return len(self.encoding.encode(text, disallowed_special=()))
