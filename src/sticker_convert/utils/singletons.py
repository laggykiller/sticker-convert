#!/usr/bin/env python3
from typing import Any, Dict, Protocol


class SingletonProtocol(Protocol):
    def close(self) -> Any: ...


class Singletons:
    def __init__(self):
        self.objs: Dict[str, SingletonProtocol] = {}

    def close(self):
        for obj in self.objs.values():
            obj.close()


singletons = Singletons()
