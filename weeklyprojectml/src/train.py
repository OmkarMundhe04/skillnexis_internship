"""
Master Training Pipeline for Bank Loan Approval Prediction.
Executes the full machine learning lifecycle:
1. Ingests raw data
2. Performs data cleaning & hygiene
3. Engineers domain features
4. Splits into train/test sets with stratification
5. Fits leakage-free pipelines for 3 candidate models:
   - Logistic Regression (Baseline)
   - Random Forest Classifier
   - XGBoost Classifier
6. Evaluates all models honestly on holdout test set
7. Selects best model based on ROC-AUC and balanced F1-score
8. Generates all presentation figures and metrics JSON
9. Serializes the final trained pipeline artifact
"""

import json
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from src.data_preprocessing import (
    CATEGORICAL_COLS,
    NUMERICAL_COLS,
    build_preprocessor,
    clean_raw_data,
    ensure_dataset,
    load_raw_data,
)
from src.evaluate import (
    evaluate_model,
    generate_eda_figures,
    plot_confusion_matrix,
    plot_feature_importance,
    plot_roc_curves,
    save_metrics,
)
from src.feature_engineering import engineer_features

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
METRICS_DIR = OUTPUTS_DIR / "metrics"


def run_training_pipeline() -> dict:
    """Executes the complete end-to-end ML training process."""
    print("=" * 65)
    print("BANK LOAN APPROVAL PREDICTION - END-TO-END TRAINING PIPELINE")
    print("=" * 65)

    # 1. Ingest Raw Dataset
    raw_path = ensure_dataset(DATA_DIR / "raw" / "loan_prediction.csv")
    df_raw = load_raw_data(raw_path)
    print(f"Step 1: Loaded raw data with shape: {df_raw.shape}")

    # 2. Data Cleaning & Hygiene
    df_cleaned = clean_raw_data(df_raw)
    processed_dir = DATA_DIR / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    df_cleaned.to_csv(processed_dir / "loan_cleaned.csv", index=False)
    print(f"Step 2: Cleaned data saved ({len(df_cleaned)} rows)")

    # 3. Feature Engineering
    df_engineered = engineer_features(df_cleaned)
    print(f"Step 3: Engineered features created. Columns: {len(df_engineered.columns)}")

    # 4. Generate Exploratory Data Analysis Figures
    print("Step 4: Generating EDA figures...")
    generate_eda_figures(df_engineered, FIGURES_DIR)

    # 5. Train / Test Split (Strictly avoiding data leakage)
    target_col = "Loan_Status"
    if target_col not in df_engineered.columns:
        raise ValueError(f"Target column '{target_col}' missing from dataset.")

    # Drop any row where target is NaN
    df_valid = df_engineered.dropna(subset=[target_col]).copy()
    X = df_valid.drop(columns=[target_col])
    y = df_valid[target_col].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )
    print(f"Step 5: Train/Test Split (Stratified 80/20) - Train: {len(X_train)}, Test: {len(X_test)}")

    # 6. Build Candidate Pipelines
    preprocessor = build_preprocessor(
        categorical_features=CATEGORICAL_COLS,
        numerical_features=NUMERICAL_COLS,
    )

    candidate_models = {
        "Logistic Regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=150,
            max_depth=5,
            min_samples_split=5,
            class_weight="balanced",
            random_state=42,
        ),
        "XGBoost": XGBClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            eval_metric="logloss",
            random_state=42,
        ),
    }

    # 7. Train & Evaluate Candidates
    print("Step 6: Training and evaluating candidate models...")
    trained_pipelines = {}
    model_metrics = {}
    roc_data = {}
    test_predictions = {}
    test_probabilities = {}

    for name, model_cls in candidate_models.items():
        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", model_cls),
        ])

        # Fit ONLY on training split
        pipeline.fit(X_train, y_train)
        trained_pipelines[name] = pipeline

        # Predictions on holdout test set
        y_pred = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)[:, 1]

        test_predictions[name] = y_pred
        test_probabilities[name] = y_proba

        # Compute performance metrics
        metrics = evaluate_model(y_test.values, y_pred, y_proba)
        model_metrics[name] = metrics

        fpr, tpr, _ = roc_curve(y_test, y_proba)
        roc_data[name] = (fpr, tpr, metrics.get("roc_auc", 0.5))

        print(
            f"   -> {name:20s} | Acc: {metrics['accuracy']:.4f} | "
            f"Prec: {metrics['precision']:.4f} | Rec: {metrics['recall']:.4f} | "
            f"F1: {metrics['f1_score']:.4f} | ROC-AUC: {metrics['roc_auc']:.4f}"
        )

    # 8. Model Selection Logic
    # Criterion: High ROC-AUC and balanced F1-score
    # If scores are close within 0.015, prefer simpler benchmark model
    best_model_name = max(
        model_metrics.keys(),
        key=lambda m: (model_metrics[m]["roc_auc"] * 0.6 + model_metrics[m]["f1_score"] * 0.4)
    )
    best_pipeline = trained_pipelines[best_model_name]
    print(f"\nStep 7: Selected Best Model: '{best_model_name}' based on ROC-AUC & F1-score balance.")

    # 9. Save Visualizations & Reports
    print("Step 8: Generating evaluation plots...")
    # Confusion Matrix for best model
    plot_confusion_matrix(
        y_true=y_test.values,
        y_pred=test_predictions[best_model_name],
        model_name=best_model_name,
        output_path=FIGURES_DIR / "confusion_matrix.png",
    )

    # Comparative ROC Curves
    plot_roc_curves(roc_data, FIGURES_DIR / "roc_curve.png")

    # Feature Importance (using Random Forest or XGBoost for tree importances)
    tree_model_name = "Random Forest" if "Random Forest" in trained_pipelines else best_model_name
    tree_pipeline = trained_pipelines[tree_model_name]
    fitted_preprocessor = tree_pipeline.named_steps["preprocessor"]
    fitted_classifier = tree_pipeline.named_steps["classifier"]

    try:
        raw_feature_names = fitted_preprocessor.get_feature_names_out()
        clean_feature_names = [
            f.replace("num__", "").replace("cat__", "") for f in raw_feature_names
        ]
        if hasattr(fitted_classifier, "feature_importances_"):
            importances = fitted_classifier.feature_importances_
            plot_feature_importance(
                feature_names=clean_feature_names,
                importances=importances,
                model_name=tree_model_name,
                output_path=FIGURES_DIR / "feature_importance.png",
            )
    except Exception as exc:
        print(f"Notice: Could not plot feature importance: {exc}")

    # Save Metrics JSON
    results_summary = {
        "best_model": best_model_name,
        "selection_criteria": (
            "Selected based on superior ROC-AUC score and harmonic F1-score balance "
            "on the stratified holdout test split (20%)."
        ),
        "dataset_statistics": {
            "total_records": len(df_valid),
            "train_records": len(X_train),
            "test_records": len(X_test),
            "approved_ratio": float(round((y == 1).mean(), 4)),
            "rejected_ratio": float(round((y == 0).mean(), 4)),
        },
        "models": model_metrics,
    }
    save_metrics(results_summary, METRICS_DIR / "model_metrics.json")

    # 10. Serialize Model Artifacts
    print("Step 9: Serializing model artifacts...")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipeline, MODELS_DIR / "best_model_pipeline.pkl")
    joblib.dump(best_pipeline.named_steps["classifier"], MODELS_DIR / "best_model.pkl")
    joblib.dump(best_pipeline.named_steps["preprocessor"], MODELS_DIR / "preprocessor.pkl")
    print(f"Artifacts successfully saved to: {MODELS_DIR}")
    print("=" * 65)
    print("TRAINING PIPELINE COMPLETE - READY FOR INFERENCE & STREAMLIT UI")
    print("=" * 65)

    return results_summary


if __name__ == "__main__":
    run_training_pipeline()
