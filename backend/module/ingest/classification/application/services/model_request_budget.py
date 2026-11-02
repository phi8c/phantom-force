"""Check complete application-owned model input without truncating source data."""
import json


class ModelRequestBudget:
    def __init__(self, *, context_window_tokens=32768, reserve_output_tokens=4096, counter=None):
        if not 0 <= reserve_output_tokens < context_window_tokens:
            raise ValueError('Invalid model request token limits')
        self.context_window_tokens = context_window_tokens
        self.reserve_output_tokens = reserve_output_tokens
        self.counter = counter

    def validate(self, system_prompt, user_prompt, *, response_format=None):
        envelope = json.dumps({'system': system_prompt, 'user': user_prompt,
                               'response_format': response_format}, ensure_ascii=False)
        # Conservative offline default, consistent with chunking's UTF-8 counter.
        # Additional margin covers chat-role/request framing owned by the provider.
        count = self.counter.count(envelope) if self.counter else len(envelope.encode('utf-8'))
        if count + 256 + self.reserve_output_tokens > self.context_window_tokens:
            raise ValueError('Complete ingestion model request exceeds configured context budget')

    @classmethod
    def from_config(cls, config):
        limits = config.pop('ingestion_request_limits', {})
        reserve = int(limits.get('reserve_output_tokens', 4096))
        for key in ('max_completion_tokens', 'max_tokens', 'max_output_tokens'):
            if config.get(key) is not None:
                reserve = max(reserve, int(config[key]))
        return cls(context_window_tokens=int(limits.get('context_window_tokens', 32768)),
                   reserve_output_tokens=reserve)
