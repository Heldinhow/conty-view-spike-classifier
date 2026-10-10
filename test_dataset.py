"""Dataset shape, determinism and paired organic-vs-bought contrast.

Paired twins are hand-worked literals (same 650 peak, only post-peak
shape differs), independent of the generator, so the test can never
pass by construction.
"""

import json
import unittest

from classifier import classify
from dataset import generate

BASE_PREFIX = [100, 102, 98, 101, 99, 103, 100, 97, 101, 99, 100, 102,
               98, 101, 100, 99, 101, 98, 100, 102, 99, 100, 98, 101]
ORGANIC_TWIN = BASE_PREFIX + [650, 520, 430, 360, 300, 250, 210, 180,
                              150, 130, 115, 108, 105, 102, 100, 99,
                              101, 100, 99, 101, 100, 99, 100, 101]
BOUGHT_TWIN = BASE_PREFIX + [650, 650, 650, 70, 65, 105, 100, 99, 101,
                             100, 99, 101, 100, 99, 101, 100, 99, 101,
                             100, 99, 101, 100, 99, 101]


class TestDatasetShape(unittest.TestCase):
    def test_balanced_200_series_of_48h(self):
        dataset = generate()
        self.assertEqual(len(dataset), 200)
        kinds = [row["kind"] for row in dataset]
        self.assertEqual(kinds.count("legitimate"), 100)
        self.assertEqual(kinds.count("suspicious"), 100)
        for row in dataset:
            with self.subTest(row=row["id"]):
                self.assertEqual(len(row["views"]), 48)
                self.assertTrue(all(isinstance(v, int) and v >= 0 for v in row["views"]))
        self.assertEqual(len({row["id"] for row in dataset}), 200)
        # JSON-serializable for the ticket-04 evaluation command.
        json.dumps(dataset)


class TestDeterminism(unittest.TestCase):
    def test_double_generate_is_byte_identical(self):
        first = json.dumps(generate(42), sort_keys=True)
        second = json.dumps(generate(42), sort_keys=True)
        self.assertEqual(first, second)

    def test_default_seed_is_42_and_seed_matters(self):
        self.assertEqual(generate(), generate(42))
        self.assertNotEqual(generate(42), generate(43))


class TestNoNetwork(unittest.TestCase):
    def test_generator_imports_no_network(self):
        with open("dataset.py") as fh:
            source = fh.read()
        for banned in ("urllib", "http", "socket", "requests", "urlopen"):
            self.assertNotIn(banned, source)


class TestPairedContrast(unittest.TestCase):
    def test_same_amplitude_opposite_buckets(self):
        self.assertEqual(len(ORGANIC_TWIN), 48)
        self.assertEqual(len(BOUGHT_TWIN), 48)
        self.assertEqual(max(ORGANIC_TWIN), max(BOUGHT_TWIN))
        organic = classify(ORGANIC_TWIN)
        bought = classify(BOUGHT_TWIN)
        self.assertEqual(organic["verdict"], "legitimate")
        self.assertNotEqual(organic["verdict"], "suspicious")
        self.assertEqual(bought["verdict"], "suspicious")


if __name__ == "__main__":
    unittest.main()
