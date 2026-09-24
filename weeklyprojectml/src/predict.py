"""
Inference and Prediction Module for Bank Loan Approval.
Loads trained serialized pipeline artifacts and serves loan predictions
with approval/rejection probabilities and risk assessments.
"""

from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
from src.feature_engineering import engineer_features

DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parent.parent / "models" / "best_model_pipeline.pkl"
)


def load_pipeline(model_path: Path | None = None):
    """
    Loads the serialized end-to-end scikit-learn Pipeline artifact.
    """
    path = model_path or DEFAULT_MODEL_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Trained model artifact not found at: {path}. "
            "Please run 'python src/train.py' first to train and save the pipeline."
        )
    return joblib.load(path)


def predict_loan(
    applicant_data: dict | pd.DataFrame,
    pipeline=None,
    model_path: Path | None = None,
) -> dict:
    """
    Takes raw applicant input dictionary or DataFrame, engineers required features,
    and runs the prediction through the trained pipeline.

    Returns:
        dict containing:
            - prediction: 1 (Approved) or 0 (Rejected)
            - prediction_label: 'Approved' or 'Rejected'
            - approval_probability: float (0.0 to 100.0)
            - rejection_probability: float (0.0 to 100.0)
            - risk_level: 'Low Risk', 'Moderate Risk', or 'High Risk'
            - key_factors: list of notable indicators
    """
    if pipeline is None:
        pipeline = load_pipeline(model_path)

    # Convert single dict to DataFrame
    if isinstance(applicant_data, dict):
        df_input = pd.DataFrame([applicant_data])
    else:
        df_input = applicant_data.copy()

    # Engineer features before passing to preprocessor pipeline
    df_engineered = engineer_features(df_input)

    # Predict class and probabilities
    pred = pipeline.predict(df_engineered)[0]
    probabilities = pipeline.predict_proba(df_engineered)[0]

    rejection_prob = round(float(probabilities[0]) * 100, 2)
    approval_prob = round(float(probabilities[1]) * 100, 2)

    # Evaluate qualitative risk
    if approval_prob >= 75.0:
        risk_level = "Low Financial Risk"
    elif approval_prob >= 50.0:
        risk_level = "Moderate Risk / Borderline"
    else:
        risk_level = "High Credit Risk"

    # Identify primary explanatory drivers
    key_factors = []
    credit_hist = df_input.get("Credit_History", [None])[0]
    if credit_hist is not None:
        if float(credit_hist) == 1.0:
            key_factors.append("Positive past credit history recorded (favorable).")
        else:
            key_factors.append("No or adverse past credit history recorded (critical risk factor).")

    income = df_engineered.get("TotalIncome", [0])[0]
    loan_amt = df_input.get("LoanAmount", [0])[0]
    ratio = df_engineered.get("IncomeLoanRatio", [0])[0]

    if pd.notnull(ratio) and ratio > 0:
        if ratio < 0.03:
            key_factors.append("High debt-to-income burden relative to monthly income.")
        else:
            key_factors.append("Healthy income buffer relative to requested principal.")

    return {
        "prediction": int(pred),
        "prediction_label": "Approved" if pred == 1 else "Not Approved",
        "approval_probability": approval_prob,
        "rejection_probability": rejection_prob,
        "risk_level": risk_level,
        "key_factors": key_factors,
        "disclaimer": (
            "Educational Machine Learning prediction. "
            "This prediction should NOT be treated as an actual banking or financial lending decision."
        ),
    }
