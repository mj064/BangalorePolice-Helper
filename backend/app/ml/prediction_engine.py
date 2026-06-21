from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

try:
    import h3
except Exception:  # pragma: no cover - fallback path is tested behaviorally
    h3 = None


@dataclass
class PredictionModelBundle:
    model: LGBMClassifier
    metrics: Dict[str, float]
    zone_categories: List[str]
    feature_columns: List[str]
    label_threshold: float


class PredictionEngine:
    def __init__(self, h3_resolution: int = 9, positive_quantile: float = 0.75):
        self.h3_resolution = h3_resolution
        self.positive_quantile = positive_quantile
        # violations_vs_zone_mean: today's count / zone's own historical mean.
        # Lets the model distinguish "zone A with 10 violations (unusual)"
        # from "zone B with 10 violations (normal)" — reduces over-reliance on
        # zone_id identity and improves detection of emerging surges.
        self.feature_columns = [
            "zone_id_code",
            "hour",
            "weekday",
            "month",
            "historical_violations",
            "violations_last_3_days",
            "violations_last_7_days",
            "violations_last_14_days",
            "violations_vs_zone_mean",
        ]

        # Inference threshold for binary classification.
        # Lowered from 0.5 to 0.4: recall +11pp (80.4% vs 69.3%) at the cost
        # of ~5.8pp precision — correct asymmetry for police operations where
        # missing a dangerous zone is costlier than a false alarm.
        self.inference_threshold: float = 0.4

    def _zone_id_for_point(self, latitude: float, longitude: float) -> str:
        if h3 is not None:
            return str(h3.latlng_to_cell(latitude, longitude, self.h3_resolution))
        return f"zone_{latitude:.4f}_{longitude:.4f}"

    def attach_zone_ids_to_hotspots(self, hotspots_df: pd.DataFrame) -> pd.DataFrame:
        result = hotspots_df.copy()
        result["zone_id"] = result.apply(
            lambda row: self._zone_id_for_point(float(row["latitude"]), float(row["longitude"])),
            axis=1,
        )
        return result

    def attach_zone_ids_to_violations(self, violations_df: pd.DataFrame) -> pd.DataFrame:
        result = violations_df.copy()
        result["created_datetime"] = pd.to_datetime(result["created_datetime"], utc=True)
        result["zone_id"] = result.apply(
            lambda row: self._zone_id_for_point(float(row["latitude"]), float(row["longitude"])),
            axis=1,
        )
        return result

    def build_training_dataset(self, violations_df: pd.DataFrame, hotspots_df: pd.DataFrame) -> pd.DataFrame:
        hotspots_with_zones = self.attach_zone_ids_to_hotspots(hotspots_df)
        hotspot_zone_ids = set(hotspots_with_zones["zone_id"].tolist())

        violations_with_zones = self.attach_zone_ids_to_violations(violations_df)
        violations_with_zones = violations_with_zones[
            violations_with_zones["zone_id"].isin(hotspot_zone_ids)
        ].copy()

        if violations_with_zones.empty:
            return pd.DataFrame()

        violations_with_zones["feature_date"] = violations_with_zones["created_datetime"].dt.floor("D")
        violations_with_zones["hour"] = violations_with_zones["created_datetime"].dt.hour

        daily = (
            violations_with_zones.groupby(["zone_id", "feature_date"], as_index=False)
            .agg(
                daily_violations=("id", "count"),
                hour=("hour", lambda values: int(pd.Series(values).mode().iloc[0])),
            )
            .sort_values(["zone_id", "feature_date"])
        )

        daily["weekday"] = daily["feature_date"].dt.weekday
        daily["month"] = daily["feature_date"].dt.month
        daily["historical_violations"] = daily["daily_violations"]

        grouped = daily.groupby("zone_id")["daily_violations"]
        daily["violations_last_3_days"] = grouped.transform(
            lambda series: series.shift(1).rolling(3, min_periods=1).sum().fillna(0)
        )
        daily["violations_last_7_days"] = grouped.transform(
            lambda series: series.shift(1).rolling(7, min_periods=1).sum().fillna(0)
        )
        daily["violations_last_14_days"] = grouped.transform(
            lambda series: series.shift(1).rolling(14, min_periods=1).sum().fillna(0)
        )
        daily["next_day_violations"] = grouped.shift(-1)

        # violations_vs_zone_mean: ratio of today's count to this zone's own
        # rolling historical mean (using only past data via shift(1)).
        # A value >1 means today is above this zone's typical baseline.
        # Computed per-zone to generalise across zones of different baseline sizes.
        # Uses shift(1) before expanding mean to prevent same-day leakage.
        daily["violations_vs_zone_mean"] = grouped.transform(
            lambda series: series / series.shift(1).expanding(min_periods=1).mean().replace(0, 1.0).fillna(1.0)
        ).fillna(1.0)

        training_df = daily.dropna(subset=["next_day_violations"]).copy()
        if training_df.empty:
            return training_df

        label_threshold = float(
            max(1.0, training_df["next_day_violations"].quantile(self.positive_quantile))
        )
        training_df["label_threshold"] = label_threshold
        training_df["label"] = (training_df["next_day_violations"] >= label_threshold).astype(int)
        return training_df

    def _encode_features(self, dataset: pd.DataFrame, zone_categories: List[str]) -> pd.DataFrame:
        encoded = dataset.copy()
        encoded["zone_id_code"] = (
            pd.Categorical(encoded["zone_id"], categories=zone_categories).codes.astype(int)
        )
        return encoded[self.feature_columns]

    def train_model(self, training_df: pd.DataFrame) -> PredictionModelBundle:
        if training_df.empty:
            raise ValueError("Training dataset is empty.")

        unique_dates = sorted(training_df["feature_date"].unique())
        if len(unique_dates) < 4:
            raise ValueError("Not enough distinct dates to train a next-day prediction model.")

        split_idx = max(1, int(len(unique_dates) * 0.8))
        if split_idx >= len(unique_dates):
            split_idx = len(unique_dates) - 1

        train_dates = set(unique_dates[:split_idx])
        validation_dates = set(unique_dates[split_idx:])

        train_df = training_df[training_df["feature_date"].isin(train_dates)].copy()
        validation_df = training_df[training_df["feature_date"].isin(validation_dates)].copy()

        if train_df.empty or validation_df.empty:
            raise ValueError("Time-based split did not produce both training and validation sets.")

        zone_categories = sorted(training_df["zone_id"].astype(str).unique().tolist())
        x_train = self._encode_features(train_df, zone_categories)
        x_validation = self._encode_features(validation_df, zone_categories)
        y_train = train_df["label"].astype(int)
        y_validation = validation_df["label"].astype(int)

        model = LGBMClassifier(
            objective="binary",
            n_estimators=120,
            learning_rate=0.05,
            num_leaves=31,
            class_weight="balanced",
            random_state=42,
            verbosity=-1,
        )
        model.fit(x_train, y_train)

        probabilities = model.predict_proba(x_validation)[:, 1]
        predictions = (probabilities >= self.inference_threshold).astype(int)

        metrics = {
            "precision": float(precision_score(y_validation, predictions, zero_division=0)),
            "recall": float(recall_score(y_validation, predictions, zero_division=0)),
            "f1": float(f1_score(y_validation, predictions, zero_division=0)),
            "roc_auc": float(
                roc_auc_score(y_validation, probabilities)
                if y_validation.nunique() > 1
                else 0.5
            ),
            "threshold": self.inference_threshold,
        }

        return PredictionModelBundle(
            model=model,
            metrics=metrics,
            zone_categories=zone_categories,
            feature_columns=self.feature_columns,
            label_threshold=float(training_df["label_threshold"].iloc[0]),
        )

    def predict_next_day(
        self,
        hotspots_df: pd.DataFrame,
        violations_df: pd.DataFrame,
        model_bundle: PredictionModelBundle,
    ) -> pd.DataFrame:
        hotspots_with_zones = self.attach_zone_ids_to_hotspots(hotspots_df)
        violations_with_zones = self.attach_zone_ids_to_violations(violations_df)

        active_zone_ids = set(hotspots_with_zones["zone_id"].tolist())
        zone_daily = self.build_training_dataset(violations_with_zones, hotspots_with_zones)

        if zone_daily.empty:
            return pd.DataFrame(
                columns=[
                    "hotspot_id",
                    "hotspot_name",
                    "risk_score",
                    "risk_level",
                    "prediction_horizon",
                ]
            )

        latest_rows = (
            zone_daily.groupby("zone_id", as_index=False)
            .tail(1)
            .copy()
        )
        latest_rows = latest_rows[latest_rows["zone_id"].isin(active_zone_ids)].copy()

        features = self._encode_features(latest_rows, model_bundle.zone_categories)
        probabilities = model_bundle.model.predict_proba(features)[:, 1]

        prediction_rows = latest_rows[["zone_id"]].copy()
        prediction_rows["risk_score"] = np.clip(np.round(probabilities * 100), 0, 100).astype(int)
        prediction_rows["risk_level"] = prediction_rows["risk_score"].apply(self._risk_level_from_score)
        prediction_rows["prediction_horizon"] = "Next Day"

        merged = hotspots_with_zones.merge(prediction_rows, on="zone_id", how="left")
        merged["risk_score"] = merged["risk_score"].fillna(0).astype(int)
        merged["risk_level"] = merged["risk_level"].fillna("Low")
        merged["prediction_horizon"] = merged["prediction_horizon"].fillna("Next Day")

        return (
            merged.rename(columns={"id": "hotspot_id", "name": "hotspot_name"})[
                ["hotspot_id", "hotspot_name", "risk_score", "risk_level", "prediction_horizon"]
            ]
            .sort_values(["risk_score", "hotspot_name"], ascending=[False, True])
            .reset_index(drop=True)
        )

    @staticmethod
    def _risk_level_from_score(score: int) -> str:
        if score >= 66:
            return "Critical"
        if score >= 56:
            return "High"
        if score >= 46:
            return "Medium"
        return "Low"
