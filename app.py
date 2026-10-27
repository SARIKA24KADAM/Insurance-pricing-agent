from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
from modeling import evaluate_pure_premium_model


st.set_page_config(
    page_title="PolicyLens | Insurance Pricing Agent",
    page_icon="📊",
    layout="wide",
)


def make_demo_data(rows: int = 1200) -> pd.DataFrame:
    """Create a reproducible, fictional policy portfolio for exploration."""
    rng = np.random.default_rng(24)
    driver_age = rng.integers(18, 81, rows)
    vehicle_age = rng.integers(0, 19, rows)
    territory = rng.choice(
        ["Urban", "Suburban", "Rural", "Coastal"], rows, p=[0.34, 0.32, 0.23, 0.11]
    )
    vehicle_type = rng.choice(
        ["Sedan", "SUV", "Pickup", "Compact"], rows, p=[0.39, 0.28, 0.17, 0.16]
    )
    use = rng.choice(["Personal", "Commute", "Business"], rows, p=[0.52, 0.38, 0.10])
    exposure = rng.uniform(0.35, 1.0, rows).round(3)

    risk = (
        (driver_age < 25) * 0.7
        + (driver_age > 72) * 0.25
        + (vehicle_age > 12) * 0.25
        + (territory == "Urban") * 0.30
        + (use == "Business") * 0.35
        + (vehicle_type == "Pickup") * 0.15
    )
    frequency_rate = 0.075 * np.exp(risk * 0.35)
    claim_count = rng.poisson(exposure * frequency_rate)
    severity_mean = 2400 + risk * 650
    incurred_losses = np.where(
        claim_count > 0,
        rng.gamma(shape=2.0, scale=severity_mean / 2.0) * claim_count,
        0.0,
    ).round(2)
    base_rate = (
        520
        + (driver_age < 25) * 180
        + (territory == "Urban") * 110
        + (use == "Business") * 140
        + (vehicle_type == "Pickup") * 75
        + (vehicle_age > 12) * 45
    )
    premium = (base_rate * exposure * rng.uniform(0.94, 1.08, rows)).round(2)

    return pd.DataFrame(
        {
            "policy_id": [f"DEMO-{i:05d}" for i in range(1, rows + 1)],
            "earned_exposure": exposure,
            "earned_premium": premium,
            "claim_count": claim_count,
            "incurred_losses": incurred_losses,
            "driver_age": driver_age,
            "vehicle_age": vehicle_age,
            "territory": territory,
            "vehicle_type": vehicle_type,
            "use": use,
        }
    )


def guess_column(columns: list[str], words: tuple[str, ...]) -> str | None:
    lowered = {column: column.lower().replace(" ", "_") for column in columns}
    for column, name in lowered.items():
        if any(word in name for word in words):
            return column
    return None


def number_or_zero(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else np.nan


def fmt_money(value: float) -> str:
    return "—" if pd.isna(value) else "$" + f"{value:,.0f}"


def fmt_percent(value: float) -> str:
    return "—" if pd.isna(value) else f"{value:.1%}"


def segment_data(
    frame: pd.DataFrame,
    factor: str,
    exposure_col: str,
    premium_col: str | None,
    count_col: str | None,
    loss_col: str | None,
) -> tuple[pd.DataFrame, str]:
    work = frame.copy()
    values = work[factor]
    if pd.api.types.is_numeric_dtype(values) and values.nunique(dropna=True) > 12:
        bins = min(5, values.nunique(dropna=True))
        work["__segment"] = pd.qcut(values, q=bins, duplicates="drop").astype("string")
        label = f"{factor} band"
    else:
        work["__segment"] = values.fillna("Missing").astype(str)
        label = factor

    aggregations: dict[str, tuple[str, str]] = {
        "Policies": (exposure_col, "size"),
        "Exposure": ("__exposure", "sum"),
    }
    if premium_col:
        aggregations["Premium"] = ("__premium", "sum")
    if count_col:
        aggregations["Claims"] = ("__claims", "sum")
    if loss_col:
        aggregations["Incurred losses"] = ("__losses", "sum")

    result = work.groupby("__segment", dropna=False).agg(**aggregations).reset_index()
    result = result.rename(columns={"__segment": label})
    if count_col:
        result["Frequency"] = result["Claims"] / result["Exposure"].replace(0, np.nan)
    if loss_col and count_col:
        result["Severity"] = result["Incurred losses"] / result["Claims"].replace(0, np.nan)
    if loss_col:
        result["Pure premium"] = result["Incurred losses"] / result["Exposure"].replace(
            0, np.nan
        )
    if loss_col and premium_col:
        result["Loss ratio"] = result["Incurred losses"] / result["Premium"].replace(
            0, np.nan
        )
    return result.sort_values("Exposure", ascending=False), label


def build_insights(
    portfolio: pd.DataFrame,
    factor_table: pd.DataFrame | None,
    factor_name: str | None,
    label: str | None,
    premium_col: str | None,
    count_col: str | None,
    loss_col: str | None,
) -> list[str]:
    insights: list[str] = []
    exposure = float(portfolio["__exposure"].sum())
    if loss_col and premium_col:
        loss_total = float(portfolio["__losses"].sum())
        premium_total = float(portfolio["__premium"].sum())
        lr = ratio(loss_total, premium_total)
        insights.append(
            f"Portfolio loss ratio is {fmt_percent(lr)} "
            f"({fmt_money(loss_total)} incurred losses on {fmt_money(premium_total)} premium)."
        )
    if count_col and exposure:
        claims = float(portfolio["__claims"].sum())
        insights.append(
            f"Observed claim frequency is {claims / exposure:.3f} claims per exposure year."
        )
    if loss_col and count_col:
        claims = float(portfolio["__claims"].sum())
        loss_total = float(portfolio["__losses"].sum())
        if claims:
            insights.append(
                f"Average incurred severity is {fmt_money(loss_total / claims)} per claim; "
                f"pure premium is {fmt_money(loss_total / exposure)} per exposure year."
            )
    if factor_table is not None and not factor_table.empty:
        metric = (
            "Loss ratio"
            if loss_col and premium_col
            else "Pure premium"
            if loss_col
            else "Frequency"
            if count_col
            else None
        )
        if metric and metric in factor_table.columns:
            ranked = factor_table.dropna(subset=[metric]).sort_values(metric)
            if len(ranked) >= 2:
                low = ranked.iloc[0]
                high = ranked.iloc[-1]
                high_value = (
                    fmt_percent(high[metric])
                    if metric == "Loss ratio"
                    else f"{high[metric]:.3f}"
                )
                insights.append(
                    f"Across {factor_name} segments, {high[label]} has the highest "
                    f"{metric.lower()} ({high_value}); {low[label]} has the lowest."
                )
            if "Policies" in factor_table and (factor_table["Policies"] < 20).any():
                insights.append(
                    "Some segments contain fewer than 20 records. Treat their estimates as less stable."
                )
    return insights


st.title("📊 PolicyLens")
st.subheader("Insurance Pricing Agent")
st.write(
    "Explore a policy portfolio, find data-quality issues, and compare rating-factor "
    "segments with a focused pricing review."
)
st.caption(
    "Analysis runs in this app session. The built-in portfolio is synthetic; uploaded data "
    "is not sent to an external AI service."
)

with st.sidebar:
    st.header("1 · Choose data")
    source = st.radio("Data source", ["Synthetic demo portfolio", "Upload a CSV"])
    uploaded = None
    if source == "Upload a CSV":
        uploaded = st.file_uploader("Choose a policy-level CSV", type=["csv"])

if source == "Upload a CSV":
    if uploaded is None:
        st.info("Upload a CSV to start. Each row should represent a policy or policy period.")
        st.stop()
    try:
        data = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"I couldn't read this CSV: {exc}")
        st.stop()
else:
    data = make_demo_data()

if data.empty:
    st.error("The selected dataset has no rows.")
    st.stop()

columns = list(data.columns)
optional_columns = ["— Not provided —", *columns]

with st.sidebar:
    st.header("2 · Map insurance fields")
    exposure_guess = guess_column(columns, ("exposure",))
    premium_guess = guess_column(columns, ("premium", "written_prem", "earned_prem"))
    count_guess = guess_column(columns, ("claim_count", "claims", "frequency"))
    loss_guess = guess_column(columns, ("incurred", "loss", "claim_amount"))

    exposure_col = st.selectbox(
        "Earned exposure (required)",
        columns,
        index=columns.index(exposure_guess) if exposure_guess in columns else 0,
        help="Use policy-years or another consistent exposure measure.",
    )

    def optional_select(label: str, guess: str | None) -> str | None:
        options = optional_columns
        index = options.index(guess) if guess in options else 0
        selected = st.selectbox(label, options, index=index)
        return None if selected == options[0] else selected

    premium_col = optional_select("Earned or written premium", premium_guess)
    count_col = optional_select("Claim count", count_guess)
    loss_col = optional_select("Incurred losses", loss_guess)
    measure_cols = {exposure_col, premium_col, count_col, loss_col}
    factor_choices = [column for column in columns if column not in measure_cols]
    factor_col = (
        st.selectbox("Compare a rating factor", factor_choices)
        if factor_choices
        else None
    )

portfolio = data.copy()
portfolio["__exposure"] = number_or_zero(portfolio[exposure_col])
portfolio["__premium"] = number_or_zero(portfolio[premium_col]) if premium_col else 0.0
portfolio["__claims"] = number_or_zero(portfolio[count_col]) if count_col else 0.0
portfolio["__losses"] = number_or_zero(portfolio[loss_col]) if loss_col else 0.0

st.markdown("### Portfolio snapshot")
st.dataframe(data.head(8), use_container_width=True, hide_index=True)

valid_exposure = portfolio["__exposure"] > 0
bad_exposure = int((~valid_exposure).sum())
if bad_exposure:
    st.warning(
        f"{bad_exposure:,} rows have missing, non-numeric, zero, or negative exposure. "
        "They are excluded from rate calculations."
    )
analysis = portfolio.loc[valid_exposure].copy()
if analysis.empty:
    st.error("No rows have positive exposure. Check the exposure-column mapping.")
    st.stop()

total_exposure = float(analysis["__exposure"].sum())
total_premium = float(analysis["__premium"].sum()) if premium_col else np.nan
total_claims = float(analysis["__claims"].sum()) if count_col else np.nan
total_losses = float(analysis["__losses"].sum()) if loss_col else np.nan
loss_ratio = ratio(total_losses, total_premium) if premium_col and loss_col else np.nan
frequency = ratio(total_claims, total_exposure) if count_col else np.nan
severity = ratio(total_losses, total_claims) if loss_col and count_col else np.nan
pure_premium = ratio(total_losses, total_exposure) if loss_col else np.nan

metric_columns = st.columns(4)
metric_columns[0].metric("Exposure", f"{total_exposure:,.1f}")
metric_columns[1].metric("Loss ratio", fmt_percent(loss_ratio))
metric_columns[2].metric(
    "Claim frequency", "—" if pd.isna(frequency) else f"{frequency:.3f}"
)
metric_columns[3].metric("Pure premium", fmt_money(pure_premium))
st.caption(
    f"Records analyzed: {len(analysis):,} · "
    f"Earned premium: {fmt_money(total_premium)} · "
    f"Average severity: {fmt_money(severity)}"
)

st.markdown("### Agent review")
quality_notes: list[str] = []
for selected_col, label in (
    (premium_col, "premium"),
    (count_col, "claim count"),
    (loss_col, "incurred loss"),
):
    if selected_col:
        values = pd.to_numeric(data[selected_col], errors="coerce")
        missing = int(values.isna().sum())
        negative = int((values < 0).sum())
        if missing:
            quality_notes.append(f"{missing:,} rows have missing or non-numeric {label}.")
        if negative:
            quality_notes.append(f"{negative:,} rows have negative {label}.")
if count_col and loss_col:
    claim_values = number_or_zero(data[count_col])
    loss_values = number_or_zero(data[loss_col])
    mismatch = int(((claim_values == 0) & (loss_values > 0)).sum())
    if mismatch:
        quality_notes.append(
            f"{mismatch:,} rows show incurred losses but a claim count of zero."
        )
if quality_notes:
    for note in quality_notes:
        st.warning(note)
else:
    st.success("No common exposure, numeric, or claim-count/loss inconsistencies were detected.")

factor_table = None
factor_label = None
if factor_col:
    factor_table, factor_label = segment_data(
        analysis, factor_col, exposure_col, premium_col, count_col, loss_col
    )

for insight in build_insights(
    analysis, factor_table, factor_col, factor_label, premium_col, count_col, loss_col
):
    st.info(insight)

if factor_table is not None:
    st.markdown(f"### Segment comparison · {factor_col}")
    display = factor_table.copy()
    if "Loss ratio" in display:
        display["Loss ratio"] = display["Loss ratio"].map(fmt_percent)
    for col in ("Premium", "Incurred losses", "Severity", "Pure premium"):
        if col in display:
            display[col] = display[col].map(fmt_money)
    if "Frequency" in display:
        display["Frequency"] = display["Frequency"].map(
            lambda value: "—" if pd.isna(value) else f"{value:.3f}"
        )
    st.dataframe(display, use_container_width=True, hide_index=True)

st.markdown("### Optional · Baseline pure-premium model")
st.write(
    "Fit an exposure-weighted Tweedie model to estimate incurred losses per exposure "
    "from selected rating factors. It compares holdout error with a simple portfolio-average baseline."
)
if not loss_col:
    st.info("Map an incurred-loss column to enable the baseline model.")
else:
    measure_columns = {exposure_col, premium_col, count_col, loss_col}
    model_features = []
    for column in columns:
        if column in measure_columns:
            continue
        name = column.lower()
        if name == "id" or name.endswith("_id") or name.endswith("_number"):
            continue
        unique_count = data[column].nunique(dropna=True)
        if unique_count < 2:
            continue
        if not pd.api.types.is_numeric_dtype(data[column]) and unique_count > 100:
            continue
        model_features.append(column)

    selected_features = st.multiselect(
        "Rating factors for the model",
        model_features,
        default=model_features[: min(5, len(model_features))],
    )
    if st.button("Fit baseline model", type="primary", disabled=not selected_features):
        try:
            evaluation = evaluate_pure_premium_model(
                data, exposure_col, loss_col, selected_features
            )
            st.caption(
                f"Holdout evaluation across {evaluation['test_records']:,} records "
                f"({evaluation['records']:,} valid records total)."
            )
            model_metrics = st.columns(3)
            model_metrics[0].metric(
                "Model weighted MAE", fmt_money(evaluation["model_mae"])
            )
            model_metrics[1].metric(
                "Portfolio baseline MAE", fmt_money(evaluation["baseline_mae"])
            )
            model_metrics[2].metric(
                "Predicted test pure premium",
                fmt_money(evaluation["predicted_test_mean"]),
            )
            improvement = (
                1 - evaluation["model_mae"] / evaluation["baseline_mae"]
                if evaluation["baseline_mae"] > 0
                else 0
            )
            if improvement > 0:
                st.success(
                    f"The model's weighted holdout error was {improvement:.1%} lower "
                    "than the portfolio-average baseline on this split."
                )
            else:
                st.info(
                    "The model did not beat the portfolio-average baseline on this split. "
                    "Review feature quality and validate with more data."
                )
        except Exception as exc:
            st.error(f"The baseline model could not be fit: {exc}")

st.caption(
    "This is a descriptive analysis prototype, not an actuarial rate indication. "
    "Review credibility, coverage mix, trend, expenses, reinsurance, and applicable regulation "
    "before using results in pricing decisions."
)

