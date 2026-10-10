"""README FP number must match a fresh re-measurement (never cache-vs-cache).

Reads the canonical line EXPECTED_FP=<0.00-1.00> from README.md via
regex and compares it against the false-positive rate obtained by
re-running the classifier nucleus over generate(42) in memory, tolerance
+/-0.005. Inconclusive never counts as a false positive.
Fails with a clear message when the README line is missing or stale
(ticket 05 owns writing the line); tampering with the number turns
this test red.
"""

import re
import unittest

from classifier import classify
from dataset import generate

TOLERANCE = 0.005


def measured_fp():
    dataset = generate(42)
    legit = [row for row in dataset if row["kind"] == "legitimate"]
    fps = sum(1 for row in legit if classify(row["views"])["verdict"] == "suspicious")
    return fps / len(legit)


class TestReadmeFp(unittest.TestCase):
    def test_readme_fp_matches_measured(self):
        try:
            with open("README.md") as fh:
                readme = fh.read()
        except FileNotFoundError:
            self.fail(
                "README.md is missing the canonical EXPECTED_FP=<0.00-1.00> "
                "line; run scripts/eval.py and record the measured rate (ticket 05)."
            )
        match = re.search(r"EXPECTED_FP=(\d\.\d+)", readme)
        self.assertIsNotNone(
            match,
            "README.md has no canonical EXPECTED_FP=<0.00-1.00> line; "
            "run scripts/eval.py and record the measured rate (ticket 05).",
        )
        declared = float(match.group(1))
        self.assertAlmostEqual(declared, measured_fp(), delta=TOLERANCE)


if __name__ == "__main__":
    unittest.main()
