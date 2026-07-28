from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional, Protocol, Tuple

from schemas.validate import validate_order


class CommandLLMClient(Protocol):
    """Return model text for a prompt; response must contain one JSON object for the order."""

    def complete(self, prompt: str) -> str: ...


def _strip_json_fences(raw: str) -> str:
    s = raw.strip()
    m = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", s, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return s


def _parse_first_json_object(raw: str) -> dict[str, Any]:
    """Parse the first top-level JSON object from model output (allows leading/trailing prose)."""
    s = _strip_json_fences(raw.strip())
    start = s.find("{")
    if start == -1:
        raise json.JSONDecodeError("expected a JSON object", s, 0)
    try:
        obj, _end = json.JSONDecoder().raw_decode(s, start)
    except Exception as e:
        raise Exception(f"Error parsing JSON: {e} {s} {start} {raw}")
    if not isinstance(obj, dict):
        raise ValueError("JSON root must be an object")
    return obj


def _prune_order_for_schema(order: Dict[str, Any]) -> None:
    wp = order.get("waypoints")
    if isinstance(wp, list) and len(wp) == 0:
        order.pop("waypoints", None)
    cons = order.get("constraints")
    if isinstance(cons, dict) and len(cons) == 0:
        order.pop("constraints", None)


def _build_parse_prompt(transcript: str) -> str:
    return f"""You convert spoken military-style unit commands into a single JSON object.

Output fields (see schemas/order.schema.json in the repo):
- units (required): array of strings, e.g. Red, Blue, Alpha, Bravo
- intent (required): one of move, hold, attack, observe, support, retreat, cancel
- waypoints: array of command cells like "A3" or "J9" when movement/attack references a grid; omit entirely if none
- constraints: optional object with preferTerrain (road|open|forest|building), stayConcealed, speed (slow|normal|fast), avoidCells
- roe: hold | return_fire | free
- posture: stand | crouch | prone
- engagement, priority, ack: only if clearly implied

Rules:
- Waypoints should be in the order the unit should reach them.

Formatting rules:
- Output exactly one JSON object, no markdown, no explanation, no code fences.
- Use lowercase enum strings as in the schema (e.g. return_fire not RETURN_FIRE).

Examples:
Transcript: "Red move to A3 via forest in A4"
{{"units":["Red"],"intent":"move","waypoints":["A3","A4"],"constraints":{{"preferTerrain":["forest"]}},"roe":"return_fire","posture":"stand"}}

Transcript: "Alpha and Bravo hold, weapons tight"
{{"units":["Alpha","Bravo"],"intent":"hold","roe":"hold","posture":"stand"}}

Now output only the JSON object for the transcript below.
Transcript: "{transcript}"
"""

## Should test that if "before" is in the transcript, it is parsed as B4 at appropriate times.

class LLMCommandParser:
    """Parse voice transcripts into structured orders using a local GGUF model (llama-cpp-python)."""

    def __init__(
        self,
        llm_client: Optional[CommandLLMClient] = None,
        *,
        model_path: Optional[str] = None,
    ) -> None:
        """Provide ``llm_client`` for tests or custom backends.

        Otherwise loads ``config/llm.yaml``: uses ``COMMANDTENT_LLM_GGUF`` if set, else
        downloads the configured Hugging Face GGUF into ``cache.directory`` when missing.
        """
        if llm_client is not None:
            self._client = llm_client
            return

        from server.orders.llm_config import get_merged_llm_config
        from server.orders.llm_download import resolve_gguf_path
        from server.orders.llm_local import LlamaCppBackend

        cfg = get_merged_llm_config()
        if model_path:
            p = os.path.abspath(model_path)
            if not os.path.isfile(p):
                raise FileNotFoundError(f"LLM weights not found: {p}")
            path = p
        else:
            path = resolve_gguf_path(cfg)

        inference = cfg.get("inference") or {}
        self._client = LlamaCppBackend(path, inference=inference)

    @property
    def llm_client(self) -> CommandLLMClient:
        return self._client

    def parse(self, text: str) -> Tuple[bool, Optional[dict], str]:
        text = text.strip()
        if not text:
            return False, None, "Empty transcript"

        prompt = _build_parse_prompt(text)

        try:
            # TODO: Turn off thinking.
            raw = self._client.complete(prompt)
        except Exception as e:
            return False, None, f"LLM inference failed: {e}"

        try:
            data = _parse_first_json_object(raw)
        except (json.JSONDecodeError, ValueError) as e:
            return False, None, f"Model did not return valid JSON: {e}"

        if not data.get("units") or not data.get("intent"):
            return False, None, "JSON missing required fields units or intent"

        _prune_order_for_schema(data)
        ok, err = validate_order(data)
        if not ok:
            return False, None, f"Order failed schema validation: {err}"

        return True, data, "Command parsed successfully"
