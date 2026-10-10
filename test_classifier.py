"""Classifier nucleus contract tests. Expected values are worked by hand from the spec."""

import unittest

from classifier import classify

STABLE = [100, 102, 98, 101, 99, 103, 100, 97]
PLATEAU = [100, 102, 98, 600, 600, 600, 55, 50]
ABRUPT = [100, 102, 98, 650, 70, 65, 105, 100]
GRAY = [100, 102, 98, 350, 300, 250, 120, 105]
ZERO_MEDIAN = [0, 0, 0, 0, 50, 0, 0, 0]
ALL_ZERO = [0] * 24
CONSTANT = [50] * 24
EDGE_FIRST = [900, 95, 100, 98, 102, 99, 101, 100]
EDGE_LAST = [100, 99, 101, 98, 102, 100, 99, 900]


class TestObviousCases(unittest.TestCase):
    def test_stable_base_is_legitimate(self):
        res = classify(STABLE)
        self.assertEqual(res["verdict"], "legitimate")
        self.assertAlmostEqual(res["signals"]["spike_ratio"], 1.03, places=3)
        self.assertAlmostEqual(res["signals"]["drop_ratio"], 0.956, places=3)
        self.assertEqual(res["signals"]["flat_score"], 0.0)
        # Same input twice gives the same output.
        self.assertEqual(classify(STABLE), res)

    def test_exact_constant_series_is_legitimate(self):
        res = classify(CONSTANT)
        self.assertEqual(res["verdict"], "legitimate")
        self.assertEqual(res["signals"]["spike_ratio"], 1.0)

    def test_bought_plateau_is_suspicious(self):
        res = classify(PLATEAU)
        self.assertEqual(res["verdict"], "suspicious")
        self.assertAlmostEqual(res["signals"]["spike_ratio"], 5.941, places=3)
        self.assertEqual(res["signals"]["flat_score"], 0.4)

    def test_abrupt_single_spike_is_suspicious(self):
        res = classify(ABRUPT)
        self.assertEqual(res["verdict"], "suspicious")
        self.assertAlmostEqual(res["signals"]["spike_ratio"], 6.5, places=3)
        self.assertAlmostEqual(res["signals"]["drop_ratio"], 0.123, places=3)
        self.assertEqual(res["signals"]["flat_score"], 0.0)


class TestGrayZone(unittest.TestCase):
    def test_gray_mid_peak_is_inconclusive(self):
        res = classify(GRAY)
        self.assertEqual(res["verdict"], "inconclusive")
        self.assertAlmostEqual(res["signals"]["spike_ratio"], 3.111, places=3)
        self.assertAlmostEqual(res["signals"]["drop_ratio"], 0.638, places=3)
        # Inconclusive never counts as a false positive: it is not suspicious.
        self.assertNotEqual(res["verdict"], "suspicious")

    def test_zero_median_is_inconclusive_never_suspicious(self):
        res = classify(ZERO_MEDIAN)
        self.assertEqual(res["verdict"], "inconclusive")
        self.assertIsNone(res["signals"]["spike_ratio"])
        self.assertEqual(res["signals"]["drop_ratio"], 0.0)
        self.assertEqual(res["signals"]["flat_score"], 0.6)

    def test_all_zero_is_inconclusive_never_raises(self):
        res = classify(ALL_ZERO)
        self.assertEqual(res["verdict"], "inconclusive")
        self.assertIsNone(res["signals"]["spike_ratio"])
        self.assertEqual(res["signals"]["drop_ratio"], 1.0)
        self.assertEqual(res["signals"]["flat_score"], 1.0)

    def test_edge_peak_is_inconclusive_never_suspicious(self):
        for series in (EDGE_FIRST, EDGE_LAST):
            with self.subTest(series=series):
                res = classify(series)
                self.assertEqual(res["verdict"], "inconclusive")
                self.assertAlmostEqual(res["signals"]["spike_ratio"], 9.0, places=3)
                self.assertNotEqual(res["verdict"], "suspicious")


class TestReason(unittest.TestCase):
    def test_reasons_cite_signals_in_plain_words(self):
        for series in (STABLE, PLATEAU, ABRUPT, GRAY, ZERO_MEDIAN, ALL_ZERO, EDGE_FIRST, EDGE_LAST, CONSTANT):
            with self.subTest(series=series):
                reason = classify(series)["reason"]
                self.assertIsInstance(reason, str)
                self.assertIn("spike_ratio", reason)
                self.assertIn("drop_ratio", reason)
                self.assertIn("flat_score", reason)
                self.assertIn("pico", reason.lower())


class TestInvalid(unittest.TestCase):
    def test_invalid_series_raise_value_error(self):
        for bad in ([], [100, -5, 100], [100, "x", 100], [100, None], [True, False],
                    [100, float("nan"), 100], [100, float("inf"), 100],
                    [100, float("-inf"), 100]):
            with self.subTest(series=bad):
                with self.assertRaises(ValueError):
                    classify(bad)


if __name__ == "__main__":
    unittest.main()
