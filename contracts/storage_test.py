# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *


class Contract(gl.Contract):
    # TreeMap/DynArray auto-initialized to empty. Do NOT assign in __init__ (Rule 2).
    notes: TreeMap[str, str]
    counters: TreeMap[str, u256]
    log: DynArray[str]

    def __init__(self):
        self.owner = "deployer"      # scalar only (Rule 2)
        self.version = "storage_test_v1"

    @gl.public.write
    def set_note(self, key: str, value: str) -> None:
        self.notes[key] = value
        self.log.append(key)

    @gl.public.write
    def bump(self, key: str, by: int) -> None:
        current = self.counters.get(key, u256(0))
        self.counters[key] = current + u256(by)

    @gl.public.view
    def get_note(self, key: str) -> str:
        return self.notes.get(key, "")

    @gl.public.view
    def get_counter(self, key: str) -> u256:
        return self.counters.get(key, u256(0))

    @gl.public.view
    def log_size(self) -> u256:
        return u256(len(self.log))
