# backend/tests/unit/test_modeling_loop.py
import datetime as dt
import pandas as pd
import pytest

from app.models.training import build_training_matrix, train_baseline_model, evaluate_model


@pytest.fixture
def sample_ml_data():
    """Generates structured features and labels sharing a (ticker_id, date) MultiIndex."""
    tickers = [1, 2, 3, 4]
    dates = pd.date_range(start="2026-01-01", periods=5, freq="D")
    mux = pd.MultiIndex.from_product([tickers, dates], names=["ticker_id", "date"])
    
    # Feature 1 (Bounded like RSI), Feature 2 (Unbounded like PE)
    features = pd.DataFrame({
        "rsi_14": [50.0 + i for i in range(20)],
        "pe_ratio": [15.0 * (1.1 ** i) for i in range(20)]
    }, index=mux)
    
    # Create matching labels (half 1s, half 0s)
    labels = pd.DataFrame({
        "label": [1, 0, 1, 0] * 5
    }, index=mux)
    
    return features, labels


def test_build_training_matrix_cleans_and_joins(sample_ml_data):
    features, labels = sample_ml_data
    
    # Inject a NaN value to mirror an technical indicator warming up
    features.iloc[0, 0] = None 
    
    train_matrix = build_training_matrix(features, labels)
    
    # 20 rows initial - 1 row due to NaN = 19 rows
    assert len(train_matrix) == 19
    assert "label" in train_matrix.columns
    assert train_matrix["label"].dtype == int


def test_train_baseline_model_defensive_checks(sample_ml_data):
    features, labels = sample_ml_data
    train_matrix = build_training_matrix(features, labels)
    
    pipeline, diagnostics = train_baseline_model(train_matrix)
    
    assert "train_accuracy" in diagnostics
    assert "train_auc" in diagnostics
    assert diagnostics["n_samples"] == 20
    
    # Inject an unhandled NaN into train_baseline_model to verify defensive flag
    train_matrix.iloc[0, 0] = None
    with pytest.raises(ValueError, match="Training features contain unexpected NaNs"):
        train_baseline_model(train_matrix)


def test_evaluate_model_ranking_precision():
    """Verifies that precision@k is calculated cross-sectionally per date."""
    # Construct an exact test state for 1 specific date across 4 tickers
    date = pd.Timestamp("2026-01-01")
    mux = pd.MultiIndex.from_tuples([(1, date), (2, date), (3, date), (4, date)], names=["ticker_id", "date"])
    
    # Dataframe contains features and labels
    test_df = pd.DataFrame({
        "feature_a": [1.0, 2.0, 3.0, 4.0],
        "label": [1, 0, 1, 0] # Ticker 1 and 3 actually beat the index
    }, index=mux)
    
    # Mock class mimicking an sklearn pipeline to explicitly control predicted probabilities
    class MockPipeline:
        def predict(self, X): return [0, 0, 1, 1]
        def predict_proba(self, X):
            # Tell the system that Ticker 3 and Ticker 4 have the highest prob of being outperformers
            return pd.DataFrame([[0.9, 0.1], [0.8, 0.2], [0.1, 0.9], [0.3, 0.7]]).values

    metrics = evaluate_model(MockPipeline(), test_df, k=2)
    
    # Our top 2 picked by probability are Ticker 3 (Label=1) and Ticker 4 (Label=0).
    # Out of 2 picks, 1 was correct -> precision@2 must be exactly 0.5
    assert metrics["mean_precision_at_2"] == 0.5