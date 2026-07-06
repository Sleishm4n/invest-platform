import logging
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, roc_auc_score

logger = logging.getLogger(__name__)

def build_training_matrix(feature_matrix: pd.DataFrame, labels_df: pd.DataFrame) -> pd.DataFrame:

    already_indexed = (
        isinstance(labels_df.index, pd.MultiIndex)
        and {"ticker_id", "date"}.issubset(set(labels_df.index.names))
    )
    labels_indexed = labels_df if already_indexed else labels_df.set_index(["ticker_id", "date"])

    initial_rows = len(feature_matrix)
    merged = feature_matrix.join(labels_indexed[["label"]], how="inner")
    joined_rows = len(merged)

    mismatched_count = initial_rows - joined_rows
    if mismatched_count > 0:
        logger.warning(f"Dropped {mismatched_count} rows due to feature/label date mismatch or lack of future horizon")

    final_df = merged.dropna().copy()
    nan_dropped_count = joined_rows - len(final_df)

    if nan_dropped_count > 0:
        logger.info(f"Dropped {nan_dropped_count} rows containing NaN feature values (e.g., indicator warm-up periods).")
        
    logger.info(f"Final usable training matrix shape: {final_df.shape}")
    
    final_df["label"] = final_df["label"].astype(int)
    return final_df

def train_baseline_model(train_df: pd.DataFrame) -> tuple[Pipeline, dict]:
    """Fits a scaled Logistic Regression pipeline on the training data.

    Enforces defensive verification checks and returns training fit diagnostics.
    """
    if train_df.empty:
        raise ValueError("Cannot train model on an empty DataFrame.")
    
    X = train_df.drop(columns=["label"])
    y = train_df["label"]

    if X.isna().any().any():
        raise ValueError("Training features contain unexpected NaNs. Data pruning failed upstream.")

    # Pipeline Construction: Handle RSI (0-100) vs PE (unbounded) scaling differences
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(random_state=42, max_iter=1000, solver="lbfgs"))
    ])

    # Fit and compute simple training diagnostics
    pipeline.fit(X, y)
    train_preds = pipeline.predict(X)
    train_probs = pipeline.predict_proba(X)[:, 1]
    
    diagnostics = {
        "train_accuracy": float(accuracy_score(y, train_preds)),
        "train_auc": float(roc_auc_score(y, train_probs)),
        "n_samples": int(len(train_df))
    }
    
    logger.info(f"Baseline model trained successfully: {diagnostics}")
    return pipeline, diagnostics


def evaluate_model(model: Pipeline, test_df: pd.DataFrame, k: int = 2) -> dict:
    """Evaluates the fitted model on testing data across global and operational

    ranking metrics (per-date cross-sectional Precision@K).
    """
    if test_df.empty:
        return {"accuracy": 0.0, "auc": 0.0, "precision_at_k": 0.0}

    X_test = test_df.drop(columns=["label"])
    y_test = test_df["label"]

    # Standard Global Metrics
    probs = model.predict_proba(X_test)[:, 1]
    preds = model.predict(X_test)
    
    metrics = {
        "global_accuracy": float(accuracy_score(y_test, preds)),
        "global_auc": float(roc_auc_score(y_test, probs)) if len(np.unique(y_test)) > 1 else np.nan
    }

    # Per-Date Cross-Sectional Precision@K (Operational Ranking Metric)
    eval_df = test_df.copy()
    eval_df["pred_prob"] = probs
    
    # Calculate precision within each specific trading session
    def _compute_date_precision(group):
        if len(group) == 0:
            return np.nan
        # If the day has fewer items than k, evaluate what's available
        actual_k = min(k, len(group))
        top_k = group.nlargest(actual_k, "pred_prob")
        return float(top_k["label"].sum() / actual_k)

    # Group by the 'date' index level and compute the cross-sectional hit-rate
    date_precisions = eval_df.groupby(level="date", group_keys=False).apply(_compute_date_precision)
    metrics[f"mean_precision_at_{k}"] = float(date_precisions.dropna().mean())

    return metrics