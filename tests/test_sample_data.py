import unittest
from pathlib import Path

import pandas as pd


class SampleInsuranceDataTests(unittest.TestCase):
    def test_sample_csv_is_synthetic_sized_and_has_expected_summary(self):
        sample_path = Path(__file__).resolve().parents[1] / "sample-insurance-data.csv"
        data = pd.read_csv(sample_path)

        self.assertEqual(len(data), 20)
        self.assertTrue(data["policy_id"].str.startswith("DEMO-").all())
        self.assertAlmostEqual(data["earned_exposure"].sum(), 17.125)
        self.assertAlmostEqual(data["earned_premium"].sum(), 12201.70)
        self.assertEqual(int(data["claim_count"].sum()), 10)
        self.assertAlmostEqual(data["incurred_losses"].sum(), 36915.00)


if __name__ == "__main__":
    unittest.main()

