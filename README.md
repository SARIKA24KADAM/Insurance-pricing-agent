# PolicyLens · Insurance Pricing Agent

A local Streamlit app for exploring insurance policy data. It checks data quality, calculates portfolio pricing metrics, compares rating-factor segments, and can fit a baseline pure-premium model.

## Run on Windows

Open PowerShell and run:

    git clone https://github.com/SARIKA24KADAM/Insurance-pricing-agent.git
    cd Insurance-pricing-agent
    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    streamlit run app.py

Streamlit will print a local URL, usually http://localhost:8501. Open it in your browser.

If PowerShell blocks virtual-environment activation, skip activation and run:

    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\streamlit.exe run app.py

## Run on macOS or Linux

    git clone https://github.com/SARIKA24KADAM/Insurance-pricing-agent.git
    cd Insurance-pricing-agent
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    streamlit run app.py

## Use the agent

1. Choose the synthetic demo portfolio, or upload a CSV.
2. Map the exposure, premium, claim-count, and incurred-loss columns in the sidebar.
3. Review loss ratio, claim frequency, severity, pure premium, data-quality notes, and segment comparisons.
4. Optionally choose rating factors and fit the baseline pure-premium model.

Each row should represent a policy or policy period. The demo data is fictional. Uploaded data is analyzed by the local app process and is not sent to an external AI service.

The model uses an exposure-weighted Tweedie regression baseline and reports a holdout comparison with a portfolio-average baseline. This prototype provides exploratory analysis, not an actuarial rate indication or production pricing recommendation. Validate assumptions and results before using them in pricing decisions.

