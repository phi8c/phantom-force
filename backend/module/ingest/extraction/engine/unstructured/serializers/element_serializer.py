from __future__ import annotations

from typing import Any


class UnstructuredElementSerializer:
    def serialize(self, element: Any) -> dict[str, Any]:
        try:
            payload = element.to_dict()
        except Exception:
            payload = {"type": type(element).__name__, "text": str(element)}

        payload["_python_class"] = type(element).__name__
        metadata = getattr(element, "metadata", None)
        if metadata is not None:
            try:
                payload["_metadata_full"] = metadata.to_dict()
            except Exception:
                pass
        return payload
