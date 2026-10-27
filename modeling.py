from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import TweedieRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def evaluate_pure_premium_model(
    data: pd.DataFrame,
    exposure_column: str,
    loss_column: str,
    feature_columns: list[str],
) -> dict[str, float | int]:
    """Fit an exposure-weighted Tweedie pure-premium baseline and holdout metrics."""
    if not feature_columns:
        raise ValueError("Choose at least one rating factor.")

    frame = data[[exposure_column, loss_column, *feature_columns]].copy()
    frame[exposure_column] = pd.to_numeric(frame[exposure_column], errors="coerce")
    frame[loss_column] = pd.to_numeric(frame[loss_column], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = frame.dropna(subset=[exposure_column, loss_column])
    frame = frame.loc[(frame[exposure_column] > 0) & (frame[loss_column] >= 0)]

    if len(frame) < 40:
        raise ValueError("At least 40 valid policy records are needed for a holdout review.")

    y = frame[loss_column] / frame[exposure_column]
    if not (y > 0).any():
        raise ValueError("The selected data has no positive incurred losses to model.")
    weights = frame[exposure_column].to_numpy(dtype=float)
    x = frame[feature_columns].copy()

    numeric_features = [
        column for column in feature_columns
        if pd.api.types.is_numeric_dtype(x[column])
    ]
    categorical_features = [
        column for column in feature_columns if column not in numeric_features
    ]
    transformers = []
    if numeric_features:
        transformers.append(
            (
                "numeric",
                Pipeline([("imputer", SimpleImputer(strategy="median"))]),
                numeric_features,
            )
        )
    if categorical_features:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("one_hot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            )
        )

    model = Pipeline(
        [
            ("features", ColumnTransformer(transformers=transformers)),
            (
                "pure_premium",
                TweedieRegressor(power=1.5, alpha=0.1, link="log", max_iter=1000),
            ),
        ]
    )

    x_train, x_test, y_train, y_test, w_train, w_test = train_test_split(
        x,
        y,
        weights,
        test_size=0.25,
        random_state=24,
    )
    model.fit(x_train, y_train, pure_premium__sample_weight=w_train)
    prediction = np.maximum(model.predict(x_test), 0)
    baseline = np.average(y_train, weights=w_train)

    return {
        "records": int(len(frame)),
        "test_records": int(len(x_test)),
        "model_mae": float(mean_absolute_error(y_test, prediction, sample_weight=w_test)),
        "baseline_mae": float(
            mean_absolute_error(
                y_test,
                np.full(len(y_test), baseline),
                sample_weight=w_test,
            )
        ),
        "observed_test_mean": float(np.average(y_test, weights=w_test)),
        "predicted_test_mean": float(np.average(prediction, weights=w_test)),
    }

