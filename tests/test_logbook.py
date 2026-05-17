"""Tests for the logbook persistence layer."""

from __future__ import annotations

from pathlib import Path

from asciiquarium import logbook


def test_in_memory_logbook_does_not_touch_disk() -> None:
    lb = logbook.in_memory()
    assert lb.path is None
    assert lb.record("fish")
    assert lb.has("fish")
    assert not lb.record("fish")  # already known


def test_logbook_round_trip(tmp_path: Path) -> None:
    p = tmp_path / "logbook.json"
    lb = logbook.Logbook(path=p)
    lb.record("ghost_whale", now=1234.5)
    lb.record("BLACK_CURRENT", now=2222.0)
    assert p.exists()
    # Reload.
    lb2 = logbook.Logbook.load(p)
    assert lb2.has("ghost_whale")
    assert lb2.has("BLACK_CURRENT")
    assert lb2.entries["ghost_whale"] == 1234.5


def test_load_handles_garbage_file(tmp_path: Path) -> None:
    p = tmp_path / "logbook.json"
    p.write_text("{ not really json", encoding="utf-8")
    lb = logbook.Logbook.load(p)
    assert lb.entries == {}


def test_load_missing_file_returns_empty(tmp_path: Path) -> None:
    p = tmp_path / "nope.json"
    lb = logbook.Logbook.load(p)
    assert lb.entries == {}


def test_all_entries_lists_unknowns_as_none(tmp_path: Path) -> None:
    lb = logbook.Logbook(path=tmp_path / "lb.json")
    lb.record("fish")
    entries = {k: ts for k, _disp, ts in lb.all_entries()}
    assert entries["fish"] is not None
    assert entries["the_sleeper"] is None
