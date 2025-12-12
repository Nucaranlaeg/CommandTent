from __future__ import annotations

import json
from jsonschema import Draft202012Validator
from pathlib import Path
from typing import Any, Dict, Tuple


def _load_order_schema() -> Dict[str, Any]:
    schema_path = Path(__file__).with_name("order.schema.json")
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


_ORDER_SCHEMA = _load_order_schema()
_VALIDATOR = Draft202012Validator(_ORDER_SCHEMA)


def validate_order(order: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a structured order against the JSON Schema.

    Returns (ok, message). On success, ok=True and message="".
    On failure, ok=False and message contains the first validation error.
    """
    errors = sorted(_VALIDATOR.iter_errors(order), key=lambda e: e.path)
    if errors:
        err = errors[0]
        path = "".join([f"/{p}" for p in err.path])
        return False, f"order invalid at {path}: {err.message}"
    return True, ""
