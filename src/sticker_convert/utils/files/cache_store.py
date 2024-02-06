#!/usr/bin/env python3
import os
import platform
import shutil
from pathlib import Path
from uuid import uuid4

if platform.system() == "Linux":
    import memory_tempfile  # type: ignore

    tempfile = memory_tempfile.MemoryTempfile(fallback=True)  # type: ignore
else:
    import tempfile

from contextlib import contextmanager
from typing import ContextManager, Optional, Union

from tempfile import TemporaryDirectory


def debug_cache_dir(path: str) -> ContextManager[Path]:
    @contextmanager
    def generator():
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
        path: Optional[str] = None,
    ) -> Union[ContextManager[Path], TemporaryDirectory[str]]:
        if path:
            return debug_cache_dir(path)
        else:
            return tempfile.TemporaryDirectory()  # type: ignore
