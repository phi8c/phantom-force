from dataclasses import dataclass

from api.ingest_orchestration import _stage_counts_payload


def test_stage_counts_payload_aggregates_without_file_details():
    payload = _stage_counts_payload(
        [
            StageCount("DOWNLOAD", "COMPLETED", 98),
            StageCount("DOWNLOAD", "PROCESSING", 2),
            StageCount("EXTRACTION", "COMPLETED", 75),
        ]
    )

    assert payload == {
        "download": {
            "completed": 98,
            "processing": 2,
        },
        "extraction": {
            "completed": 75,
        },
    }


@dataclass(frozen=True)
class StageCount:
    stage: str
    status: str
    count: int
