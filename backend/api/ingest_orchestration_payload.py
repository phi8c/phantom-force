"""Pure response mapping, independent of route/database initialization."""


def stage_counts_payload(stage_counts):
    stages: dict[str, dict[str, int]] = {}
    for count in stage_counts:
        stages.setdefault(count.stage.lower(), {})[count.status.lower()] = count.count
    return stages
