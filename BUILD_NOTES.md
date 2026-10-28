# How PolicyLens Was Built

## 1. Purpose

PolicyLens is a small, local-first insurance pricing analysis agent. It helps a data scientist explore policy-level experience, catch common data problems, compare rating-factor segments, and evaluate a simple pure-premium model.

The first version was designed around a clear workflow: load a dataset, map its insurance fields, review portfolio metrics, inspect segments, and optionally fit a baseline model. It is an exploratory analysis tool, not an automated pricing decision system.

![PolicyLens workflow from data selection through analysis and optional modeling](docs/agent-workflow.svg)

*Figure 1. The end-to-end analysis workflow in the Streamlit app.*

## 2. What “agent” means in this version

This version combines an analysis workflow with a statistical machine-learning model:

- Deterministic analysis code calculates portfolio metrics and produces short findings from those results.
- A Tweedie regression model can estimate expected incurred losses per unit of exposure from selected rating factors.
- The app presents the results in an interactive Streamlit interface.

There is no conversational LLM, external AI API, or autonomous pricing action in this version. The uploaded dataset is processed in the running app process.

## 3. Technology choices

- Python is used for the analysis and application logic.
- Streamlit provides the browser-based interface and file-upload controls.
- pandas and NumPy handle tabular data, calculations, and reproducible synthetic examples.
- scikit-learn provides preprocessing, train/test splitting, and the Tweedie regression baseline.

The app can run on a laptop and does not require a database, API key, or cloud service.

## 4. Project files

- **app.py** builds the interface and runs the portfolio workflow.
- **modeling.py** prepares data, fits the pure-premium model, and calculates holdout metrics.
- **requirements.txt** lists the Python packages needed to run the app.
- **sample-insurance-data.csv** is a small fictional file for trying the CSV upload.
- **README.md** contains setup and usage instructions.
- **BUILD_NOTES.md** explains the design and implementation in more depth.

## 5. Data workflow

### Choose a source

The sidebar offers either a built-in synthetic portfolio or a user-supplied CSV. The built-in data generator uses a fixed random seed so its example portfolio is reproducible. The separate sample CSV contains 20 fictional policy records and is useful for trying the upload workflow.

### Map the columns

The interface tries to recognize column names for:

- Earned exposure
- Earned or written premium
- Claim count
- Incurred losses

The user can change each mapping. Exposure is required. Premium, claim count, and incurred losses are optional, but more mapped fields enable more metrics. Other columns can be selected as rating factors.

Each row should represent one policy or policy period. Exposure should be positive and expressed consistently, such as policy-years.

### Standardize numeric values

Mapped numeric columns are converted to numbers for analysis. Values that cannot be converted become missing and are treated as zero for aggregations; the quality review separately reports missing or non-numeric values. Rows with non-positive exposure are excluded from rate calculations and counted in a warning.

### Calculate portfolio metrics

When the relevant columns are available, the app calculates:

- **Loss ratio** = incurred losses ÷ premium
- **Claim frequency** = claim count ÷ exposure
- **Claim severity** = incurred losses ÷ claim count
- **Pure premium** = incurred losses ÷ exposure

Records and total exposure are shown separately because they are different measures.

### Review data quality

The app checks for missing or non-numeric premium, claim count, and incurred-loss values; negative values in those fields; rows with positive losses but zero claims; and rows with invalid exposure. These are initial checks rather than a complete actuarial or source-system validation.

### Compare rating-factor segments

The user chooses one field to compare. Categorical values are summarized as groups. Numeric fields with more than 12 distinct values are divided into up to five quantile bands. The table reports the measures available from the mapped columns, such as exposure, premium, claims, frequency, severity, pure premium, and loss ratio.

The generated review identifies the highest and lowest segment for the most relevant available metric. It also flags segments with fewer than 20 records as potentially less stable. This threshold is a practical warning in the prototype, not a formal credibility standard.

## 6. Baseline pure-premium model

The optional model estimates incurred losses per unit of exposure from selected rating factors.

![Baseline pure-premium modeling pipeline](docs/model-pipeline.svg)

*Figure 2. The baseline model pipeline and its holdout comparison.*

1. Rows need positive exposure and non-negative incurred losses. At least 40 valid rows are required.
2. The target is incurred losses divided by exposure.
3. Rows are split into 75% training and 25% holdout data using a fixed random seed.
4. Exposure is supplied as a sample weight so a policy with more exposure contributes proportionately to fitting and evaluation.
5. Numeric predictors have missing values filled with their median. Categorical predictors have missing values filled with their most common value, then are one-hot encoded.
6. A scikit-learn TweedieRegressor with power 1.5 and a log link is fit on the training set.
7. Holdout weighted mean absolute error is compared with a simple portfolio-average pure-premium baseline.

The model is a baseline for exploration. A lower holdout error on one random split does not establish that a model is stable, fair, actuarially adequate, or suitable for production.

## 7. Running the app

Follow the operating-system commands in **README.md**. In brief, create a Python virtual environment, install packages from **requirements.txt**, and start the app with Streamlit. The terminal prints the local browser address.

To explore the sample file, select **Upload a CSV** and choose **sample-insurance-data.csv**. To try the model with enough records, start with the larger built-in synthetic portfolio; the 20-row sample is intentionally small.

## 8. Privacy and data handling

The app has no outbound AI or analytics calls. In a local run, the uploaded CSV is read into the running Python process and is not written to a project data file. If the app is later deployed to a hosted server, uploaded data will be processed on that server; deployment and access controls should be reviewed before uploading confidential information.

## 9. Current limitations and next steps

- The app currently accepts CSV files, not Excel workbooks or direct database connections.
- It does not account for coverage mix, policy limits, deductibles, inflation trend, expenses, commissions, reinsurance, or state and provincial constraints.
- The pure-premium model has one train/test split and a simple baseline; it does not provide cross-validation, calibration plots, uncertainty intervals, fairness review, or formal actuarial credibility.
- Findings are descriptive and should be checked against the source data and domain knowledge.
- The app does not set or recommend an individual customer's price.

Possible next steps are to add schema diagnostics, repeatable validation, model diagnostics, downloadable reports, more granular segment controls, and an optional natural-language interface over the computed results.

