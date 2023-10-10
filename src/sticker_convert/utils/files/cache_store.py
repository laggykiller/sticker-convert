#!/usr/bin/env python3
import os
import platform
import shutil
from uuid import uuid4

if platform.system() == "Linux":
    import memory_tempfile  # type: ignore

    tempfile = memory_tempfile.MemoryTempfile(fallback=True)
else:
    import tempfile
import contextlib
from typing import Optional


@contextlib.contextmanager
def debug_cache_dir(path: str):
    path_random = os.path.join(path, str(uuid4()))
    os.mkdir(path_random)
    try:
        yield path_random
    finally:
        shutil.rmtree(path_random)


class CacheStore:
    @staticmethod
    def get_cache_store(path: Optional[str] = None):
        if path:
            return debug_cache_dir(path)
        else:
            return tempfile.TemporaryDirectory()
