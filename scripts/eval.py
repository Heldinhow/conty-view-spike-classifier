"""Single evaluation command: generate the dataset and measure the FP rate.

Generates data/dataset.json with the fixed seed, re-runs the classifier
nucleus over it (never cache-vs-cache) and prints plus persists the
false-positive rate (suspicious over total legitimate; inconclusive
never counts as a false positive nor as a suspicious hit). Also
reports the inconclusive rate over legitimate without failing.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classifier import classify
from dataset import generate

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def main():
    args = _parse()
    dataset = generate(args.seed)
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "dataset.json"), "w") as fh:
        json.dump(dataset, fh)
    legit = [row for row in dataset if row["kind"] == "legitimate"]
    verdicts = [classify(row["views"])["verdict"] for row in legit]
    flagged = sum(1 for v in verdicts if v == "suspicious")
    fp = flagged / len(legit)
    inconclusive = sum(1 for v in verdicts if v == "inconclusive") / len(legit)
    with open(os.path.join(DATA, "expected_fp.txt"), "w") as fh:
        fh.write("%.4f\n" % fp)
    print("seed=%d series=%d legitimate=%d" % (args.seed, len(dataset), len(legit)))
    print("false-positive rate: %.4f (%d/%d legitimate flagged suspicious)"
          % (fp, flagged, len(legit)))
    print("inconclusive rate over legitimate: %.4f (reported only, never fails)"
          % inconclusive)


def _parse():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    main()
