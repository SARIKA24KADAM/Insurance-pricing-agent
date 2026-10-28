# How PolicyLens Was Built

## Purpose and scope

PolicyLens is a local-first insurance pricing analysis prototype. It lets a data scientist load policy-level experience, map core fields, review data quality, compare one rating factor at a time, and optionally evaluate a baseline pure-premium model.

The app is an interactive analysis workflow with deterministic findings and a statistical model. It does not use an LLM, call an external AI API, or autonomously set prices.

![PolicyLens workflow from data selection through analysis and optional modeling](docs/agent-workflow.svg)

*Figure 1. The implemented Streamlit workflow.*

## Architecture and tools

- `app.py` provides Streamlit UI, synthetic portfolio generation, CSV upload, field mapping, portfolio calculations, segment summaries, and result display.
- `modeling.py` builds the scikit-learn preprocessing pipeline, fits Tweedie regression, and evaluates holdout errors.
- pandas and NumPy handle tabular data, calculations, and reproducible synthetic data.
- scikit-learn provides imputers, one-hot encoding, train/test splitting, Tweedie regression, and weighted MAE.
- Streamlit runs the user interface locally.

The app needs no database, API key, or cloud model. Uploaded data is read into the current Python process and is not saved to a project data file by the app.

## Workflow

1. The user chooses the built-in synthetic portfolio or uploads a CSV.
2. The interface attempts to identify exposure, premium, claim count, and incurred-loss columns. The user can change the mappings.
3. Numeric values are coerced for calculations. Invalid values become missing and are treated as zero in the current aggregations; quality warnings report missing/nonnumeric values for mapped premium, claim, and loss fields. Non-positive exposure is excluded from rate calculations.
4. Portfolio measures are calculated where the required mappings exist.
5. The user selects a rating factor for segment summaries. Numeric factors with more than 12 distinct values are split into up to five quantile bins. Small segments under 20 records receive a stability warning.
6. Optionally, a Tweedie model is fit on selected features and evaluated on a holdout sample.

Each record should represent one policy or policy period, with exposure in consistent units such as policy-years.

## Measures

- Loss ratio = incurred losses ÷ premium.
- Claim frequency = claim count ÷ exposure.
- Claim severity = incurred losses ÷ claim count.
- Pure premium = incurred losses ÷ exposure.

These portfolio ratios are aggregates, not averages of per-policy ratios. A missing or zero denominator produces an unavailable result where guarded in the app.

## Synthetic examples

The built-in data generator produces 1,200 fictional records with a fixed NumPy random seed (24). The included CSV contains 20 fictional example policies for trying upload, mapping, and summary behavior. It is deliberately too small for the model's 40-record minimum. [sample-results.md](docs/sample-results.md) gives its computed portfolio summary.

## Baseline model

![Baseline pure-premium modeling pipeline](docs/model-pipeline.svg)

*Figure 2. The model and holdout evaluation flow.*

1. Rows must have positive exposure and non-negative incurred losses; at least 40 eligible rows are required.
2. The target is incurred losses divided by exposure.
3. Rows are split into 75% training and 25% holdout data using random seed 24.
4. Exposure is passed as a sample weight during model fitting and weighted evaluation.
5. Numeric predictors use median imputation. Categorical predictors use most-frequent imputation followed by one-hot encoding.
6. A scikit-learn TweedieRegressor with power 1.5, log link, alpha 0.1, and at most 1,000 iterations is fit.
7. Holdout weighted mean absolute error is compared with a weighted portfolio-average target calculated from the training records.

One random split does not establish stability, fairness, actuarial adequacy, or production readiness.

## Error handling and configuration

The app catches CSV-read errors and model-fitting errors and displays them in the UI. It reports an empty dataset, non-positive exposure, and invalid model input. Dependencies are listed in `requirements.txt`. There are no application environment variables today; `.env.example` records that explicitly.

## Privacy and security

The app has no outbound model or analytics API calls. A local upload is processed in memory by the app process and is not written into the repository. A hosted deployment would process files on its server, so hosting access controls and retention policies must be reviewed before sensitive data is uploaded. The committed CSV is fictional. Git ignore rules cover environment secrets, virtual environments, caches, and common model artifacts.

## Tests

`tests/test_modeling.py` covers successful model evaluation, filtering of ineligible rows, minimum record validation, and the requirement for positive losses. `tests/test_sample_data.py` checks expected totals from the fictional sample CSV. The GitHub Actions workflow runs these tests on Python 3.11 and 3.12. These tests do not validate every Streamlit interaction or actuarial assumptions.

## Limitations and future improvements

Current limits include CSV-only upload, basic data checks, one selected segment factor at a time, a single holdout split, and no uncertainty, calibration, fairness, or formal credibility analysis. The prototype also omits coverage mix, limits, deductibles, trend, expenses, reinsurance, and jurisdiction-specific pricing rules.

Useful future steps include stronger schema validation, repeated model validation and diagnostics, downloadable reports, richer segment controls, and a grounded natural-language interface if one is added later.


