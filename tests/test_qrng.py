"""Tests for the quantum RNG fallback path.

We don't hit the network in CI: the tests verify the offline fallback
returns a usable :class:`random.Random` even when the upstream API is
unreachable, and that an explicit seed always wins.
"""

from __future__ import annotations

import random

from asciiquarium import qrng


def test_make_rng_honors_explicit_seed() -> None:
    r1 = qrng.make_rng(seed=42)
    r2 = qrng.make_rng(seed=42)
    assert isinstance(r1, random.Random)
    # Same seed -> identical streams.
    assert [r1.random() for _ in range(5)] == [r2.random() for _ in range(5)]


def test_make_rng_falls_back_without_network(monkeypatch) -> None:
    monkeypatch.setattr(qrng, "fetch_quantum_seed", lambda **_kw: None)
    r = qrng.make_rng(prefer_quantum=True)
    assert isinstance(r, random.Random)
    # Should be a usable RNG (random() in [0, 1)).
    v = r.random()
    assert 0.0 <= v < 1.0


def test_make_rng_uses_quantum_seed_when_available(monkeypatch) -> None:
    monkeypatch.setattr(qrng, "fetch_quantum_seed", lambda **_kw: 0xDEADBEEF)
    r = qrng.make_rng(prefer_quantum=True)
    # Same as random.Random(0xDEADBEEF).
    ref = random.Random(0xDEADBEEF)
    assert [r.random() for _ in range(3)] == [ref.random() for _ in range(3)]


def test_fetch_quantum_seed_returns_none_on_urlopen_failure(monkeypatch) -> None:
    import urllib.error

    def _boom(*_args, **_kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(qrng.urllib.request, "urlopen", _boom)
    assert qrng.fetch_quantum_seed(timeout=0.1) is None


def test_fetch_quantum_seed_returns_none_on_malformed_payload(monkeypatch) -> None:
    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b'{"success": true, "data": "not-a-list"}'

    monkeypatch.setattr(qrng.urllib.request, "urlopen", lambda *a, **k: _Resp())
    assert qrng.fetch_quantum_seed(timeout=0.1) is None


def test_fetch_quantum_seed_packs_data_into_integer(monkeypatch) -> None:
    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b'{"success": true, "data": [1, 2, 3]}'

    monkeypatch.setattr(qrng.urllib.request, "urlopen", lambda *a, **k: _Resp())
    seed = qrng.fetch_quantum_seed(timeout=0.1)
    # Three 16-bit words packed: ((1 << 16) | 2) << 16 | 3
    assert seed == ((1 << 16) | 2) << 16 | 3
