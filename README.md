# Insurance Pricing Agent

A local Streamlit MVP for reviewing policy-level insurance pricing data. It profiles a dataset, checks common data-quality problems, calculates core portfolio metrics, compares rating-factor segments, and writes a short pricing review.

## Run locally

1. Create and activate a Python virtual environment.
2. Install dependencies with pip install -r requirements.txt.
3. Start the app with streamlit run app.py.
4. Use the included synthetic demo data or upload a CSV file.

The demo data is fictional. Uploaded data is processed by the local app process; this version does not send data to an external AI service.

## Expected data

Each row should represent a policy or policy-period. Map the columns for earned exposure, premium, claim count, and incurred losses. At least an exposure column is needed. For the most complete analysis, include all four measures and one or more rating factors such as territory, vehicle type, or driver age.

The agent reports descriptive portfolio and segment statistics. It does not recommend or set actual customer prices. Validate results with actuarial, regulatory, and business review before using them for pricing decisions.

