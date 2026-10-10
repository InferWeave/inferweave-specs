"""Regression test: transactional runtime lifecycle (IW-RT-003, specs/50)."""
import re
import unittest
from pathlib import Path

DOC = Path(__file__).resolve().parents[2] / "state-machines" / "runtime.md"

STATES = [
    "DISCOVERED", "RESOLVING", "PREPARING", "DOWNLOADING", "RESERVING", "STARTING",
    "LOADING", "WARMING", "VALIDATING", "READY", "BUSY", "IDLE", "DRAINING",
    "UNLOADING", "STOPPED", "FAILED",
]
PRE_SERVING = ["RESOLVING", "PREPARING", "DOWNLOADING", "RESERVING", "STARTING",
               "LOADING", "WARMING", "VALIDATING"]

REQUIRED = {
    ("DISCOVERED", "RESOLVING"), ("RESOLVING", "PREPARING"),
    ("PREPARING", "DOWNLOADING"), ("DOWNLOADING", "PREPARING"),
    ("PREPARING", "RESERVING"), ("RESERVING", "STARTING"), ("STARTING", "LOADING"),
    ("LOADING", "WARMING"), ("WARMING", "VALIDATING"), ("VALIDATING", "READY"),
    ("READY", "BUSY"), ("BUSY", "READY"), ("READY", "IDLE"), ("IDLE", "READY"),
    ("BUSY", "IDLE"), ("IDLE", "BUSY"),
    ("READY", "DRAINING"), ("BUSY", "DRAINING"), ("IDLE", "DRAINING"),
    ("DRAINING", "READY"), ("DRAINING", "UNLOADING"),
    ("READY", "FAILED"), ("BUSY", "FAILED"), ("IDLE", "FAILED"),
    ("DRAINING", "FAILED"), ("UNLOADING", "STOPPED"), ("UNLOADING", "FAILED"),
    ("DISCOVERED", "FAILED"), ("DISCOVERED", "STOPPED"),
} | {(s, "FAILED") for s in PRE_SERVING} | {(s, "STOPPED") for s in PRE_SERVING}


class InvalidTransition(Exception):
    """Typed error for forbidden lifecycle transitions."""


def load_table():
    text = DOC.read_text()
    block = re.search(r"Allowed transitions:\s*```text\n(.*?)```", text, re.S).group(1)
    table = {}
    for line in block.strip().splitlines():
        src, dst = line.split("->")
        table[src.strip()] = {d.strip() for d in dst.split("|") if d.strip()}
    return table


def transition(table, src, dst):
    if dst not in table.get(src, set()):
        raise InvalidTransition(f"{src} -> {dst}")
    return dst


class RuntimeLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.table = load_table()

    def test_states_enumerated_in_dependency_order(self):
        text = DOC.read_text()
        positions = [text.index(f"`{s}`") for s in STATES]
        assert positions == sorted(positions)
        assert set(self.table) == set(STATES)

    def test_required_transitions_present(self):
        allowed = {(s, d) for s, ds in self.table.items() for d in ds}
        missing = REQUIRED - allowed
        assert not missing, f"missing transitions: {sorted(missing)}"
        assert allowed == REQUIRED, f"unexpected: {sorted(allowed - REQUIRED)}"

    def test_forbidden_transitions_rejected(self):
        count = 0
        for src in STATES:
            for dst in STATES:
                if (src, dst) in REQUIRED:
                    assert transition(self.table, src, dst) == dst
                else:
                    with self.assertRaises(InvalidTransition):
                        transition(self.table, src, dst)
                    count += 1
        assert count > 0
        try:
            transition(self.table, "RESOLVING", "READY")
            raised = False
        except InvalidTransition:
            raised = True
        assert raised

    def test_terminal_states_absorbing(self):
        assert self.table["FAILED"] == set()
        assert self.table["STOPPED"] == set()

    def test_no_return_to_ready_after_unload(self):
        assert "READY" not in self.table["UNLOADING"]
        assert self.table["UNLOADING"] == {"STOPPED", "FAILED"}
        assert "READY" in self.table["DRAINING"]  # cancel before unload only

    def test_ready_only_via_validation(self):
        sources = {s for s, ds in self.table.items() if "READY" in ds}
        assert sources == {"VALIDATING", "BUSY", "IDLE", "DRAINING"}


if __name__ == "__main__":
    unittest.main()
