"""Tests for the lore-fragment system."""

from __future__ import annotations

import random

from asciiquarium import lore


def test_disabled_lore_never_emits() -> None:
    st = lore.LoreState(enabled=False)
    rng = random.Random(0)
    for _ in range(10_000):
        out = lore.tick(st, 1.0, rng)
        assert out is None
    assert st.pending is None


def test_lore_emits_after_min_interval() -> None:
    st = lore.LoreState(enabled=True, next_eligible=10.0, since_last=1e9)
    rng = random.Random(0)
    # Step past the min interval; expect at least one fragment.
    fired = []
    for _ in range(2000):
        out = lore.tick(st, 1.0, rng, min_interval=30.0)
        if out is not None:
            fired.append(out)
    assert fired, "expected at least one lore fragment over a long run"


def test_burst_guard_prevents_back_to_back() -> None:
    """Force-emit a fragment then ensure a second one can't fire within
    the burst guard window."""
    st = lore.LoreState(enabled=True, next_eligible=0.0, since_last=1e9)
    rng = random.Random(1)
    out1 = lore.tick(st, 1.0, rng, min_interval=30.0, burst_guard=45.0)
    assert out1 is not None
    # Even with next_eligible reset to 0, since_last is 0 so burst guard blocks.
    st.next_eligible = 0.0
    out2 = lore.tick(st, 1.0, rng, min_interval=30.0, burst_guard=45.0)
    assert out2 is None


def test_min_floor_is_enforced() -> None:
    """``min_interval`` below MIN_FLOOR is clamped up to MIN_FLOOR."""
    st = lore.LoreState(enabled=True, next_eligible=0.0, since_last=1e9)
    rng = random.Random(2)
    lore.tick(st, 1.0, rng, min_interval=1.0, burst_guard=1.0)
    # Next eligible must be >= MIN_FLOOR.
    assert st.next_eligible >= lore.MIN_FLOOR


def test_preferred_tags_get_higher_weight() -> None:
    """With preferred_tags='signal' the emitted fragment should be tagged
    'signal' more than half the time across many samples."""
    rng = random.Random(7)
    tag_counts: dict[str, int] = {}
    preferred = frozenset({"signal"})
    for _ in range(2000):
        f = lore._pick_fragment(rng, preferred)
        tag_counts[f.tag] = tag_counts.get(f.tag, 0) + 1
    total = sum(tag_counts.values())
    # Signal tag should be at least 35% of picks (3x weight vs 1x).
    assert tag_counts.get("signal", 0) / total >= 0.35
