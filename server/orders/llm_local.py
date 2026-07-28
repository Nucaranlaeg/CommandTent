"""Load a local GGUF model via llama-cpp-python for command JSON generation."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


class LlamaCppBackend:
    """Mmaps and runs a GGUF weights file; implements ``complete(prompt) -> str``."""

    def __init__(self, model_path: str, inference: Optional[Dict[str, Any]] = None) -> None:
        inf = inference or {}
        self._max_tokens = int(inf.get("max_tokens", 512))
        self._temperature = float(inf.get("temperature", 0.1))
        self._opts: dict[str, Any] = {
            "model_path": model_path,
            "n_ctx": int(inf.get("n_ctx", 4096)),
            "n_gpu_layers": int(inf.get("n_gpu_layers", 0)),
            "verbose": bool(inf.get("verbose", False)),
        }
        threads_raw = os.environ.get("COMMANDTENT_LLM_N_THREADS", "").strip()
        if threads_raw:
            self._opts["n_threads"] = int(threads_raw)
        self._llm: Any = None

    def _ensure_loaded(self) -> None:
        if self._llm is not None:
            return
        try:
            from llama_cpp import Llama
        except ImportError as e:
            raise ImportError(
                "llama-cpp-python is required for local LLM parsing. "
                "Install with: pip install llama-cpp-python"
            ) from e
        self._llm = Llama(
            **self._opts,
            chat_handler_kwargs={"enable_thinking": False},
        )

    def complete(self, prompt: str) -> str:
        self._ensure_loaded()
        out = self._llm.create_completion(
            prompt=prompt,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            echo=False,
            reasoning_budget=0,
        )
        return str(out["choices"][0]["text"])
