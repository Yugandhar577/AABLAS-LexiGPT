import json
from typing import Any


def safe_json_load(s: str) -> Any:
    try:
        return json.loads(s)
    except Exception:
        return None