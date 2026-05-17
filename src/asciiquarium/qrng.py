"""Quantum random number generation with an offline fallback.

This module exposes helpers that try to seed a :class:`random.Random` instance
from the ANU public quantum RNG service (https://qrng.anu.edu.au/), falling
back to the operating system's secure CSPRNG (``os.urandom`` via
``random.SystemRandom``) when the service is unreachable, blocked, or returns
an unexpected payload.

The network fetch is best-effort, has a short timeout, and is silent on
failure: aquariums must boot offline. Only the standard library is used, so
no new dependencies are introduced.
"""

from __future__ import annotations

import json
import logging
import random
import secrets
import urllib.error
import urllib.request

_LOG = logging.getLogger(__name__)

# Public, no-API-key JSON endpoint that returns ``length`` uint16 samples
# drawn from a live quantum vacuum source.
QRNG_URL = "https://qrng.anu.edu.au/API/jsonI.php?length={length}&type=uint16"
DEFAULT_TIMEOUT = 2.0
DEFAULT_LENGTH = 8  # 8 * 16 = 128 bits of entropy -> plenty for a Random seed


def fetch_quantum_seed(
    *, length: int = DEFAULT_LENGTH, timeout: float = DEFAULT_TIMEOUT
) -> int | None:
    """Fetch a seed from the ANU quantum RNG service.

    Returns ``None`` on any failure (network error, non-200, malformed
    response). The return value is a non-negative integer suitable for
    :class:`random.Random`.
    """
    if length <= 0:
        return None
    url = QRNG_URL.format(length=length)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            if getattr(resp, "status", 200) != 200:
                return None
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        _LOG.debug("quantum RNG fetch failed: %s", exc)
        return None
    if not isinstance(payload, dict) or not payload.get("success"):
        return None
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return None
    seed = 0
    for word in data:
        try:
            seed = (seed << 16) | (int(word) & 0xFFFF)
        except (TypeError, ValueError):
            return None
    return seed


def make_rng(
    seed: int | None = None,
    *,
    prefer_quantum: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> random.Random:
    """Construct a :class:`random.Random` for the aquarium.

    Behavior:

    * If ``seed`` is provided, it is honored as-is for reproducibility.
    * Else if ``prefer_quantum`` is true, try to fetch a seed from ANU.
    * Else, or on quantum-fetch failure, fall back to a non-deterministic
      OS-entropy seed (``secrets.randbits``), giving callers a different
      aquarium every launch without reaching the network.
    """
    if seed is not None:
        return random.Random(seed)
    if prefer_quantum:
        qseed = fetch_quantum_seed(timeout=timeout)
        if qseed is not None:
            return random.Random(qseed)
    # Offline fallback: cryptographically strong, locally generated.
    return random.Random(secrets.randbits(128))
