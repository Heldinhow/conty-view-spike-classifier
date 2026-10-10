"""Seeded synthetic dataset: 200 series of 48h, balanced halves.

Legitimate half: stable base plus organic viral with gradual decay and
noise. Suspicious half: bought peak with mechanical plateau and abrupt
drop. Deterministic standard library only (random.Random); no network.
Internal detail of the future single evaluation command (ticket 04),
which will call generate(seed).
"""

import random

SERIES = 48
LEGIT = "legitimate"
SUSPICIOUS = "suspicious"


def generate(seed=42):
    """Build the full dataset deterministically.

    Returns a JSON-serializable list of {id, kind, views}.
    """
    rng = random.Random(seed)
    dataset = []
    for i in range(50):
        dataset.append({"id": "legit-%03d" % i, "kind": LEGIT, "views": _stable(rng)})
    for i in range(50, 100):
        dataset.append({"id": "legit-%03d" % i, "kind": LEGIT, "views": _organic(rng)})
    for i in range(100, 150):
        dataset.append({"id": "suspicious-%03d" % (i - 100), "kind": SUSPICIOUS,
                        "views": _plateau(rng)})
    for i in range(150, 200):
        dataset.append({"id": "suspicious-%03d" % (i - 100), "kind": SUSPICIOUS,
                        "views": _abrupt(rng)})
    rng.shuffle(dataset)
    return dataset


def _base(rng):
    return [100 + rng.randint(-5, 5) for _ in range(SERIES)]


def _peak_pos(rng):
    return rng.randint(18, 26)


def _stable(rng):
    return _base(rng)


def _organic(rng):
    views = _base(rng)
    at = _peak_pos(rng)
    peak = rng.randint(580, 720)
    views[at] = peak
    for k in range(1, SERIES - at):
        decayed = int(peak * (0.82 ** k)) + rng.randint(-3, 3)
        if decayed <= 115:
            break
        views[at + k] = decayed
    if views[at - 1] == views[at - 2]:
        views[at - 1] += 2
    return views


def _plateau(rng):
    views = _base(rng)
    at = _peak_pos(rng)
    peak = rng.randint(580, 720)
    views[at] = peak
    views[at + 1] = peak
    views[at + 2] = peak
    views[at + 3] = rng.randint(60, 80)
    views[at + 4] = rng.randint(60, 80)
    return views


def _abrupt(rng):
    views = _base(rng)
    at = _peak_pos(rng)
    peak = rng.randint(580, 720)
    views[at] = peak
    views[at + 1] = rng.randint(60, 80)
    views[at + 2] = rng.randint(60, 80)
    views[at + 3] = rng.randint(95, 110)
    return views
