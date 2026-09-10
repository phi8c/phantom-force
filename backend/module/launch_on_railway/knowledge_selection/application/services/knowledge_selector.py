import json
import logging
from time import perf_counter

from module.ai.llm.composition import LLMGateway
from module.ingest.knowledge.composition import (
    KnowledgeDiscoveredRequest,
)
from module.prompt.composition import PromptProvider

from module.launch_on_railway.knowledge_selection.application.dtos.knowledge_selection_result import (
    KnowledgeSelection,
    KnowledgeSelectionResult,
)
from module.launch_on_railway.knowledge_selection.application.enums.knowledge_selection_enums import (
    KnowledgeSelectionModelCode,
    KnowledgeSelectionPromptCode,
    KnowledgeSelectionProviderCode,
)


logger = logging.getLogger(__name__)


class KnowledgeSelector:

    def __init__(
        self,
        prompt_provider: PromptProvider,
        llm_gateway: LLMGateway,
    ):
        self._prompt_provider = prompt_provider
        self._llm_gateway = llm_gateway

    async def select(
        self,
        *,
        question: str,
        knowledge_candidates: list[KnowledgeDiscoveredRequest],
    ) -> KnowledgeSelectionResult:

        started_at = perf_counter()
        logger.info(
            "[KNOWLEDGE_SELECTION] start knowledge_candidate_count=%s",
            len(knowledge_candidates),
        )

        step_started_at = perf_counter()
        prompt = await self._prompt_provider.get_by_code(
            KnowledgeSelectionPromptCode.SELECT_KNOWLEDGE.value,
        )
        logger.info(
            "[KNOWLEDGE_SELECTION] prompt_load_done elapsed_ms=%s found=%s",
            int((perf_counter() - step_started_at) * 1000),
            prompt is not None,
        )
        if prompt is None:
            raise ValueError(
                "Knowledge selection prompt not found or disabled"
            )

        config = dict(prompt.configuration or {})
        response_format = config.pop(
            "response_format",
            {"type": "json_object"},
        )

        user_prompt = self._build_user_prompt(
            question=question,
            knowledge_candidates=knowledge_candidates,
        )
        step_started_at = perf_counter()
        logger.info(
            "[KNOWLEDGE_SELECTION] llm_start user_prompt_chars=%s",
            len(user_prompt),
        )
        llm_result = await self._llm_gateway.generate(
            provider_code=(
                KnowledgeSelectionProviderCode.AZURE_OPENAI.value
            ),
            model_code=(
                KnowledgeSelectionModelCode.SELECT_KNOWLEDGE.value
            ),
            system_prompt=prompt.system_prompt,
            user_prompt=user_prompt,
            response_format=response_format,
            config=config,
        )
        logger.info(
            "[KNOWLEDGE_SELECTION] llm_done elapsed_ms=%s finish_reason=%s usage=%s",
            int((perf_counter() - step_started_at) * 1000),
            llm_result.finish_reason,
            llm_result.usage,
        )
        if not llm_result.content:
            raise ValueError(
                "Empty knowledge selection response"
            )

        raw_response = json.loads(llm_result.content)
        if not isinstance(raw_response, dict):
            raise ValueError(
                "Knowledge selection response must be a JSON object"
            )

        selections = self._parse_selections(
            raw_response.get("selections", []),
            knowledge_candidates=knowledge_candidates,
        )

        logger.info(
            "[KNOWLEDGE_SELECTION] selected_request_ids=%s "
            "selected_information_types=%s selected_topics=%s selected_fields=%s",
            [selection.request_id for selection in selections],
            [
                selection.information_type_codes
                for selection in selections
            ],
            [selection.topic_codes for selection in selections],
            [selection.field_codes for selection in selections],
        )
        logger.info(
            "[KNOWLEDGE_SELECTION] done elapsed_ms=%s",
            int((perf_counter() - started_at) * 1000),
        )

        return KnowledgeSelectionResult(
            selections=selections,
            raw_response=raw_response,
        )

    @classmethod
    def _parse_selections(
        cls,
        raw_selections,
        *,
        knowledge_candidates: list[KnowledgeDiscoveredRequest],
    ) -> list[KnowledgeSelection]:

        if not isinstance(raw_selections, list):
            return []

        candidates_by_id = {
            candidate.request_id: candidate
            for candidate in knowledge_candidates
        }
        selections: list[KnowledgeSelection] = []
        for raw_selection in raw_selections:
            if not isinstance(raw_selection, dict):
                continue

            request_id = (
                raw_selection.get("request_id")
            )
            if request_id is None:
                continue

            request_id = str(request_id)
            if request_id not in candidates_by_id:
                continue

            candidate = candidates_by_id[request_id]
            information_type_codes = cls._validated_codes(
                raw_selection.get("information_type_codes", []),
                {
                    item.code
                    for item in candidate.available_information_types
                },
            )
            topic_codes = cls._validated_codes(
                raw_selection.get("topic_codes", []),
                {
                    item.code
                    for item in candidate.available_topics
                },
            )
            field_codes = cls._validated_codes(
                raw_selection.get("field_codes", []),
                {
                    item.code
                    for item in candidate.available_fields
                },
            )
            if (
                information_type_codes is None
                or topic_codes is None
                or field_codes is None
            ):
                continue

            constraints = raw_selection.get("constraints", {})
            if not isinstance(constraints, dict):
                constraints = {}

            selections.append(
                KnowledgeSelection(
                    request_id=str(request_id),
                    information_type_codes=information_type_codes,
                    topic_codes=topic_codes,
                    field_codes=field_codes,
                    constraints=constraints,
                )
            )

        return selections

    @staticmethod
    def _validated_codes(
        raw_codes,
        available_codes: set[str],
    ) -> list[str] | None:

        if not isinstance(raw_codes, list):
            return None

        result = []
        for raw_code in raw_codes:
            code = str(raw_code)
            if code not in available_codes:
                return None
            if code not in result:
                result.append(code)
        return result

    @classmethod
    def _build_user_prompt(
        cls,
        *,
        question: str,
        knowledge_candidates: list[KnowledgeDiscoveredRequest],
    ) -> str:

        return json.dumps(
            {
                "question": question,
                "knowledge_candidates": [
                    cls._candidate_payload(candidate)
                    for candidate in knowledge_candidates
                ],
                "response_contract": {
                    "selections": {
                        "type": "array",
                        "item": {
                            "request_id": "string from knowledge_candidates",
                            "information_type_codes": (
                                "array of available information type codes"
                            ),
                            "topic_codes": (
                                "array of available topic codes"
                            ),
                            "field_codes": (
                                "array of available field codes"
                            ),
                            "constraints": "object",
                        },
                    },
                },
            },
            ensure_ascii=False,
            default=str,
        )

    @classmethod
    def _candidate_payload(
        cls,
        candidate: KnowledgeDiscoveredRequest,
    ) -> dict:

        return {
            "request_id": candidate.request_id,
            "need": candidate.need,
            "original_seeds": candidate.original_seeds,
            "matched_entry_points": {
                "objects": [
                    cls._object_payload(item)
                    for item in candidate.matched_entry_points.objects
                ],
                "information_types": [
                    cls._code_payload(item)
                    for item in (
                        candidate
                        .matched_entry_points
                        .information_types
                    )
                ],
                "topics": [
                    cls._code_payload(item)
                    for item in candidate.matched_entry_points.topics
                ],
                "fields": [
                    cls._code_payload(item)
                    for item in candidate.matched_entry_points.fields
                ],
            },
            "available_objects": [
                cls._object_payload(item)
                for item in candidate.available_objects
            ],
            "available_information_types": [
                cls._code_payload(item)
                for item in candidate.available_information_types
            ],
            "available_topics": [
                cls._code_payload(item)
                for item in candidate.available_topics
            ],
            "available_fields": [
                cls._code_payload(item)
                for item in candidate.available_fields
            ],
            "constraints": candidate.constraints,
        }

    @staticmethod
    def _object_payload(item) -> dict:

        return {
            "object_code": item.object_code,
            "identifier_code": item.identifier_code,
            "name": item.name,
            "identifier_name": item.identifier_name,
            "description": item.description,
        }

    @staticmethod
    def _code_payload(item) -> dict:

        return {
            "code": item.code,
            "name": item.name,
            "description": item.description,
            "data_type": item.data_type,
        }
