"""Resolve path to the command GGUF, downloading from Hugging Face if needed."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from server.orders.llm_config import cache_directory_abs, get_merged_llm_config


def _min_valid_bytes() -> int:
    raw = os.environ.get("COMMANDTENT_LLM_MIN_FILE_BYTES", "").strip()
    if not raw:
        return 1_000_000
    return int(raw.replace("_", ""), 10)


def resolve_gguf_path(cfg: Dict[str, Any] | None = None) -> str:
    """Return absolute path to the weights file.

    If ``COMMANDTENT_LLM_GGUF`` is set, that path is used (must exist).

    Otherwise the file under ``cache.directory`` / ``huggingface.filename`` is used;
    if missing or too small, it is downloaded from ``huggingface.repo_id``.
    """
    explicit = os.environ.get("COMMANDTENT_LLM_GGUF", "").strip()
    if explicit:
        p = Path(explicit)
        if not p.is_file():
            raise FileNotFoundError(f"COMMANDTENT_LLM_GGUF is not a file: {explicit}")
        return str(p.resolve())

    cfg = cfg or get_merged_llm_config()
    hf = cfg.get("huggingface") or {}
    repo_id = hf.get("repo_id")
    filename = hf.get("filename")
    if not repo_id or not filename:
        raise ValueError("config/llm.yaml must set huggingface.repo_id and huggingface.filename")

    cache_root = cache_directory_abs(cfg)
    cache_root.mkdir(parents=True, exist_ok=True)
    target = cache_root / filename

    if target.is_file() and target.stat().st_size >= _min_valid_bytes():
        return str(target.resolve())

    try:
        from huggingface_hub import hf_hub_download
    except ImportError as e:
        raise ImportError(
            "huggingface_hub is required to download the default GGUF. "
            "Install with: pip install huggingface_hub"
        ) from e

    hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=str(cache_root),
        local_dir_use_symlinks=False,
    )

    if not target.is_file():
        matches = list(cache_root.rglob(filename))
        if len(matches) == 1:
            return str(matches[0].resolve())
        raise FileNotFoundError(
            f"Download finished but {filename} not found under {cache_root}"
        )

    if target.stat().st_size < _min_valid_bytes():
        raise OSError(f"Downloaded file looks truncated: {target}")

    return str(target.resolve())
