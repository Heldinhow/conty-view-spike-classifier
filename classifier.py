"""View spike classifier nucleus.

Pure standard library. Takes an hourly views series and returns a verdict,
a readable reason and the signals used. Deterministic: no IO, no clock,
no randomness.
"""

from math import isfinite
from statistics import median

HIGH_SPIKE = 5.0
MID_SPIKE = 3.0
ABRUPT_DROP = 0.4
FLAT_HIGH = 0.4
_POST_WINDOW = 3
_FLAT_BEFORE = 2
_FLAT_AFTER = 3


def _validate(views):
    if not isinstance(views, list) or not views:
        raise ValueError("views must be a non-empty list")
    for value in views:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or value < 0
        ):
            raise ValueError("views must contain only non-negative numbers")


def classify(views):
    """Classify one hourly views series.

    Returns {"verdict": legitimate|suspicious|inconclusive,
    "reason": readable motive citing the signals,
    "signals": {"spike_ratio", "drop_ratio", "flat_score"}}.
    """
    _validate(views)
    total = len(views)
    peak = max(views)
    at = views.index(peak)
    baseline = median(views)
    if baseline == 0:
        post = views[at + 1 :]
        drop = round(sum(post[:_POST_WINDOW]) / len(post[:_POST_WINDOW]) / peak, 3) if post else 1.0
        flat = _flat_score(views, at)
        return {
            "verdict": "inconclusive",
            "reason": (
                "série com mediana zerada, sem baseline para medir o pico "
                f"(spike_ratio=inf, drop_ratio={drop}, flat_score={flat}); "
                "inconclusivo por falta de referência, nunca suspeito."
            ),
            "signals": {"spike_ratio": float("inf"), "drop_ratio": drop, "flat_score": flat},
        }
    spike = round(peak / baseline, 3)
    post = views[at + 1 :]
    drop = round(sum(post[:_POST_WINDOW]) / len(post[:_POST_WINDOW]) / peak, 3) if post else 1.0
    flat = _flat_score(views, at)
    if at == 0 or at == total - 1:
        return {
            "verdict": "inconclusive",
            "reason": (
                f"pico de {spike}x na borda temporal, sem baseline ou sem pós-pico "
                f"para medir a queda (spike_ratio={spike}, drop_ratio={drop}, "
                f"flat_score={flat}); inconclusivo, nunca suspeito."
            ),
            "signals": {"spike_ratio": spike, "drop_ratio": drop, "flat_score": flat},
        }
    if spike >= HIGH_SPIKE and (drop <= ABRUPT_DROP or flat >= FLAT_HIGH):
        if drop <= ABRUPT_DROP and flat >= FLAT_HIGH:
            trigger = f"queda abrupta (drop_ratio={drop}) e platô mecânico (flat_score={flat})"
        elif drop <= ABRUPT_DROP:
            trigger = f"queda abrupta pós-pico (drop_ratio={drop}, flat_score={flat})"
        else:
            trigger = f"platô mecânico (flat_score={flat}, drop_ratio={drop})"
        return {
            "verdict": "suspicious",
            "reason": (
                f"pico comprado: pico de {spike}x sobre a mediana "
                f"(spike_ratio={spike}) com {trigger}."
            ),
            "signals": {"spike_ratio": spike, "drop_ratio": drop, "flat_score": flat},
        }
    if MID_SPIKE <= spike < HIGH_SPIKE:
        return {
            "verdict": "inconclusive",
            "reason": (
                f"zona cinzenta: pico de {spike}x sobre a mediana "
                f"(spike_ratio={spike}) com decaimento médio "
                f"(drop_ratio={drop}, flat_score={flat}); prefiro não acusar."
            ),
            "signals": {"spike_ratio": spike, "drop_ratio": drop, "flat_score": flat},
        }
    return {
        "verdict": "legitimate",
        "reason": (
            f"base estável: pico de apenas {spike}x sobre a mediana "
            f"(spike_ratio={spike}), sem queda abrupta (drop_ratio={drop}) "
            f"nem repetição mecânica (flat_score={flat})."
        ),
        "signals": {"spike_ratio": spike, "drop_ratio": drop, "flat_score": flat},
    }


def _flat_score(views, at):
    """Share of equal adjacent pairs in a small window around the peak."""
    window = views[max(0, at - _FLAT_BEFORE) : at + _FLAT_AFTER + 1]
    if len(window) < 2:
        return 0.0
    same = sum(1 for a, b in zip(window, window[1:]) if a == b)
    return round(same / (len(window) - 1), 3)
