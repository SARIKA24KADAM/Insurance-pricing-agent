import unittest

import numpy as np
import pandas as pd

from modeling import evaluate_pure_premium_model


class EvaluatePurePremiumModelTests(unittest.TestCase):
    def setUp(self):
        self.data = pd.DataFrame(
            {
                "exposure": np.ones(80),
                "losses": np.where(np.arange(80) % 4 == 0, 0.0, 100.0 + np.arange(80)),
                "age": np.arange(80) % 60 + 18,
                "territory": np.where(np.arange(80) % 2, "urban", "rural"),
            }
        )

    def test_returns_holdout_metrics_for_numeric_and_categorical_features(self):
        result = evaluate_pure_premium_model(
            self.data, "exposure", "losses", ["age", "territory"]
        )

        self.assertEqual(result["records"], 80)
        self.assertEqual(result["test_records"], 20)
        self.assertGreaterEqual(result["model_mae"], 0)
        self.assertGreaterEqual(result["baseline_mae"], 0)
        self.assertTrue(np.isfinite(result["predicted_test_mean"]))

    def test_excludes_rows_with_invalid_exposure_or_losses(self):
        data = pd.concat(
            [
                self.data.iloc[:42],
                pd.DataFrame(
                    {
                        "exposure": [0, -1, np.nan, np.inf],
                        "losses": [100, 100, 100, 100],
                        "age": [30, 31, 32, 33],
                        "territory": ["rural"] * 4,
                    }
                ),
                pd.DataFrame(
                    {
                        "exposure": [1, 1],
                        "losses": [-1, np.nan],
                        "age": [34, 35],
                        "territory": ["urban"] * 2,
                    }
                ),
            ],
            ignore_index=True,
        )

        result = evaluate_pure_premium_model(
            data, "exposure", "losses", ["age", "territory"]
        )
        self.assertEqual(result["records"], 42)

    def test_requires_at_least_40_valid_records(self):
        with self.assertRaisesRegex(ValueError, "At least 40"):
            evaluate_pure_premium_model(
                self.data.iloc[:39], "exposure", "losses", ["age"]
            )

    def test_rejects_data_without_positive_losses(self):
        data = self.data.copy()
        data["losses"] = 0
        with self.assertRaisesRegex(ValueError, "no positive incurred losses"):
            evaluate_pure_premium_model(data, "exposure", "losses", ["age"])

    def test_requires_at_least_one_feature(self):
        with self.assertRaisesRegex(ValueError, "at least one rating factor"):
            evaluate_pure_premium_model(self.data, "exposure", "losses", [])


if __name__ == "__main__":
    unittest.main()


