import tiktoken

from app.application.chunking.contracts.token_counter import (
    TokenCounter,
)


class TiktokenCounter(
    TokenCounter,
):

    def __init__(
        self,
        model_name: str,
    ):
        self.encoding = (
            tiktoken.encoding_for_model(
                model_name,
            )
        )

    def count(
        self,
        text: str,
    ) -> int:

        return len(
            self.encoding.encode(
                text,
            )
        )