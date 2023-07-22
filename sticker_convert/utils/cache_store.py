#!/usr/bin/env python3
import os
import sys
import shutil
from uuid import uuid4
if sys.platform == 'linux':
    import memory_tempfile
    tempfile = memory_tempfile.MemoryTempfile(fallback=True)
else:
    import tempfile
import contextlib

@contextlib.contextmanager
def debug_cache_dir(path):
    path_random = os.path.join(path, str(uuid4()))
    os.mkdir(path_random)
    try:
        yield path_random
    finally:
        shutil.rmtree(path_random)

class CacheStore:
    def get_cache_store(path=None):
        if path:
            return debug_cache_dir(path)
        else:
            return tempfile.TemporaryDirectory()