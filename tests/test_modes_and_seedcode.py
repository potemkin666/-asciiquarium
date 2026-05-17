"""Tests for mode dispatcher and seed-code round-trip."""

from __future__ import annotations

import pytest

from asciiquarium import modes
from asciiquarium.seedcode import SeedCode, parse


def test_all_modes_resolve_to_preset() -> None:
    for name in modes.ALL_MODES:
        preset = modes.resolve(name)
        assert preset.mode == name
        assert isinstance(preset.fps, int)
        assert preset.fps > 0


def test_classic_mode_disables_all_abyss_features() -> None:
    p = modes.resolve(modes.CLASSIC)
    assert p.events_enabled is False
    assert p.rare_creatures_enabled is False
    assert p.lore_enabled is False
    assert p.mood_pinned is True
    assert p.crt_scanlines is False


def test_abyss_mode_enables_abyss_features() -> None:
    p = modes.resolve(modes.ABYSS)
    assert p.events_enabled is True
    assert p.rare_creatures_enabled is True
    assert p.lore_enabled is True


def test_nightwatch_preset_has_crt_and_low_fps() -> None:
    p = modes.resolve(modes.NIGHTWATCH)
    assert p.crt_scanlines is True
    assert p.fps <= 12
    assert p.events_enabled is True


def test_sumi_e_preset_pins_dreaming_mood() -> None:
    p = modes.resolve(modes.SUMI_E)
    assert p.ink_wash is True
    assert p.mood_pinned is True


def test_unknown_mode_raises() -> None:
    with pytest.raises(ValueError):
        modes.resolve("does-not-exist")


# ---- Seed code ----


def test_seed_code_round_trip() -> None:
    original = SeedCode(biome="trench", seed=777, mood="haunted", modifier="KOI")
    code = original.serialize()
    assert code == "TRENCH-777-HAUNTED-KOI"
    parsed = parse(code)
    assert parsed == original
    # Re-serialise yields the same string.
    assert parsed.serialize() == code


def test_seed_code_without_modifier() -> None:
    sc = SeedCode(biome="reef", seed=42, mood="calm")
    code = sc.serialize()
    assert code == "REEF-42-CALM"
    assert parse(code) == sc


def test_seed_code_case_insensitive_parse() -> None:
    parsed = parse("trench-77-haunted")
    assert parsed.biome == "trench"
    assert parsed.mood == "haunted"


def test_seed_code_rejects_unknown_biome() -> None:
    with pytest.raises(ValueError):
        parse("NOT_A_BIOME-1-CALM")


def test_seed_code_rejects_unknown_mood() -> None:
    with pytest.raises(ValueError):
        parse("reef-1-NOT_A_MOOD")


def test_seed_code_rejects_bad_seed() -> None:
    with pytest.raises(ValueError):
        parse("reef-abc-calm")


def test_seed_code_rejects_wrong_arity() -> None:
    with pytest.raises(ValueError):
        parse("reef-1-calm-koi-extra")
    with pytest.raises(ValueError):
        parse("reef-1")
    with pytest.raises(ValueError):
        parse("")
