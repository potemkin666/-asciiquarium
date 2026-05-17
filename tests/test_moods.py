"""Tests for mood transition determinism and gating."""

from __future__ import annotations

import random

from asciiquarium import moods


def test_all_moods_have_specs() -> None:
    for name in moods.ALL_MOODS:
        assert name in moods.MOODS
        spec = moods.get_mood(name)
        assert spec.name == name
        assert 0.0 <= spec.fish_spawn_mult <= 5.0
        assert 0.0 <= spec.bubble_density_mult <= 5.0


def test_pick_next_mood_deterministic_with_seed() -> None:
    r1 = random.Random(42)
    r2 = random.Random(42)
    seq1 = [moods.pick_next_mood(moods.CALM, r1) for _ in range(20)]
    seq2 = [moods.pick_next_mood(moods.CALM, r2) for _ in range(20)]
    assert seq1 == seq2


def test_pick_next_mood_returns_valid_mood() -> None:
    rng = random.Random(7)
    current = moods.CALM
    for _ in range(200):
        nxt = moods.pick_next_mood(current, rng)
        assert moods.is_valid_mood(nxt)
        current = nxt


def test_pick_next_mood_eventually_drifts_back_to_calm() -> None:
    """Calm is the gravitational center: across many steps, we should
    revisit it from any starting mood."""
    rng = random.Random(1)
    for start in moods.ALL_MOODS:
        cur = start
        saw_calm = False
        for _ in range(400):
            cur = moods.pick_next_mood(cur, rng)
            if cur == moods.CALM:
                saw_calm = True
                break
        assert saw_calm, f"never reached calm from {start}"


def test_unknown_mood_returns_calm_spec() -> None:
    spec = moods.get_mood("not_a_mood")
    assert spec.name == moods.CALM


def test_mood_transitions_self_dominant() -> None:
    """Self-weight is highest in the default table: a mood tends to stay."""
    rng = random.Random(123)
    cur = moods.STORMING
    same = 0
    n = 200
    for _ in range(n):
        nxt = moods.pick_next_mood(cur, rng)
        if nxt == cur:
            same += 1
        cur = nxt
    # At least 30% of steps should be self-transitions for a self-weight of 4.
    assert same >= n * 0.25
