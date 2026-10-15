#!/usr/bin/env python3
from __future__ import annotations

import os
import platform
import shutil
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, ContextManager, Generator
from uuid import uuid4

if platform.system() == "Linux":
    import memory_tempfile  # type: ignore

    tempfile = memory_tempfile.MemoryTempfile(fallback=True)  # type: ignore
else:
    import tempfile


def debug_cache_dir(path: str) -> ContextManager[Path]:
    @contextmanager
    def generator() -> Generator[Any, Any, Any]:
        path_random = Path(path, str(uuid4()))
        os.mkdir(path_random)
        try:
            yield path_random
        finally:
            shutil.rmtree(path_random)

    return generator()


class CacheStore:
    @staticmethod
    def get_cache_store(
        path: str | None = None,
    ) -> ContextManager[Path] | TemporaryDirectory[str]:
        if path:
            return debug_cache_dir(path)
        return tempfile.TemporaryDirectory()  # type: ignore
