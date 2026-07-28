"""Load ``config/llm.yaml`` and merge optional ``COMMANDTENT_LLM_*`` overrides."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LLM_CONFIG_PATH = PROJECT_ROOT / "config" / "llm.yaml"


def _deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in overrides.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        elif v is not None:
            out[k] = v
    return out


def load_llm_yaml() -> Dict[str, Any]:
    if not _LLM_CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Missing LLM config: {_LLM_CONFIG_PATH}")
    with _LLM_CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("config/llm.yaml must contain a mapping at the root")
    return data


def _env_inference_overrides() -> Dict[str, Any]:
    patch: Dict[str, Any] = {}
    inf: Dict[str, Any] = {}

    if os.environ.get("COMMANDTENT_LLM_N_CTX", "").strip():
        inf["n_ctx"] = int(os.environ["COMMANDTENT_LLM_N_CTX"].strip())
    if os.environ.get("COMMANDTENT_LLM_N_GPU_LAYERS", "").strip():
        inf["n_gpu_layers"] = int(os.environ["COMMANDTENT_LLM_N_GPU_LAYERS"].strip())
    if os.environ.get("COMMANDTENT_LLM_MAX_TOKENS", "").strip():
        inf["max_tokens"] = int(os.environ["COMMANDTENT_LLM_MAX_TOKENS"].strip())
    if os.environ.get("COMMANDTENT_LLM_TEMPERATURE", "").strip():
        inf["temperature"] = float(os.environ["COMMANDTENT_LLM_TEMPERATURE"].strip())
    v = os.environ.get("COMMANDTENT_LLM_VERBOSE", "").strip().lower()
    if v in ("1", "true", "yes"):
        inf["verbose"] = True
    elif v in ("0", "false", "no"):
        inf["verbose"] = False

    if inf:
        patch["inference"] = inf
    return patch


def _env_model_overrides() -> Dict[str, Any]:
    patch: Dict[str, Any] = {}
    repo = os.environ.get("COMMANDTENT_LLM_HF_REPO", "").strip()
    fn = os.environ.get("COMMANDTENT_LLM_HF_FILE", "").strip()
    cache_dir = os.environ.get("COMMANDTENT_LLM_CACHE_DIR", "").strip()
    hf: Dict[str, Any] = {}
    cache: Dict[str, Any] = {}
    if repo:
        hf["repo_id"] = repo
    if fn:
        hf["filename"] = fn
    if hf:
        patch["huggingface"] = hf
    if cache_dir:
        cache["directory"] = cache_dir
    if cache:
        patch["cache"] = cache
    return patch


def get_merged_llm_config() -> Dict[str, Any]:
    """YAML defaults merged with ``COMMANDTENT_LLM_*`` environment overrides."""
    base = load_llm_yaml()
    merged = _deep_merge(base, _env_inference_overrides())
    merged = _deep_merge(merged, _env_model_overrides())
    return merged


def cache_directory_abs(cfg: Dict[str, Any]) -> Path:
    rel = (cfg.get("cache") or {}).get("directory", ".cache/llm")
    p = Path(rel)
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()
