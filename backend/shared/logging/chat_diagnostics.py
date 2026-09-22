import json
from dataclasses import asdict
from dataclasses import is_dataclass
from pathlib import Path
from threading import Lock
from typing import Any


_TRACE_PATH = Path(__file__).resolve().parents[2] / "temp" / "chat_trace.log"
_TRACE_LOCK = Lock()


def print_chat_trace(stage: str, value: Any) -> None:
    def serialize(item: Any) -> Any:
        if is_dataclass(item) and not isinstance(item, type):
            return asdict(item)
        return str(item)

    rendered = (
        value
        if isinstance(value, str)
        else json.dumps(
            value,
            ensure_ascii=False,
            default=serialize,
            indent=2,
        )
    )
    block = (
        f"===== CHAT {stage} START =====\n"
        f"{rendered}\n"
        f"===== CHAT {stage} END =====\n"
    )
    with _TRACE_LOCK:
        print(block, end="", flush=True)
        try:
            _TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with _TRACE_PATH.open("a", encoding="utf-8") as trace_file:
                trace_file.write(block)
        except OSError as exc:
            print(f"[CHAT_TRACE] file_write_failed error={exc}", flush=True)
