from __future__ import annotations

from ..models import SectionModel


class SectionMetricsProcessor:
    def process(self, sections: list[SectionModel]) -> None:
        for section in sections:
            self._calculate(section)

    def _calculate(self, section: SectionModel) -> tuple[str, int]:
        aggregated_content = section.content
        token_count = self._estimate_tokens(section.content)
        aggregated_token_count = token_count

        for child in section.children:
            child_content, child_tokens = self._calculate(child)
            if child_content:
                separator = "\n\n" if aggregated_content else ""
                aggregated_content += separator + child_content
            aggregated_token_count += child_tokens

        section.token_count = token_count
        section.aggregated_content = aggregated_content
        section.aggregated_token_count = aggregated_token_count
        return aggregated_content, aggregated_token_count

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return len(text.split()) if text else 0
