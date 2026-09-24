"""
Model Evaluation and Visualization Module.
Computes evaluation metrics (Accuracy, Precision, Recall, F1, ROC-AUC)
and generates presentation-ready visualizations.
"""

import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray,
                   y_proba: np.ndarray | None = None) -> dict[str, float]:
    """
    Computes standard classification evaluation metrics.
    All metrics are rounded to 4 decimal places.
    """
    metrics = {
        "accuracy": float(round(accuracy_score(y_true, y_pred), 4)),
        "precision": float(round(precision_score(y_true, y_pred, zero_division=0), 4)),
        "recall": float(round(recall_score(y_true, y_pred, zero_division=0), 4)),
        "f1_score": float(round(f1_score(y_true, y_pred, zero_division=0), 4)),
    }

    if y_proba is not None:
        try:
            metrics["roc_auc"] = float(round(roc_auc_score(y_true, y_proba), 4))
        except Exception:
            metrics["roc_auc"] = float("nan")
    else:
        metrics["roc_auc"] = float("nan")

    return metrics


def save_metrics(metrics: dict, output_path: Path) -> None:
    """Saves evaluation metrics dictionary as formatted JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)
    print(f"Metrics saved to: {output_path}")


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray,
                          model_name: str, output_path: Path) -> None:
    """
    Plots a 2x2 confusion matrix with TN, FP, FN, TP cell annotations.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cm = confusion_matrix(y_true, y_pred)

    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        xticklabels=["Rejected (0)", "Approved (1)"],
        yticklabels=["Rejected (0)", "Approved (1)"],
        ax=ax,
        annot_kws={"size": 14, "weight": "bold"},
    )

    # Detailed breakdown labels
    labels = [
        [f"TN: {cm[0, 0]}", f"FP: {cm[0, 1]}"],
        [f"FN: {cm[1, 0]}", f"TP: {cm[1, 1]}"],
    ]
    for i in range(2):
        for j in range(2):
            ax.text(
                j + 0.5,
                i + 0.72,
                labels[i][j],
                ha="center",
                va="center",
                color="darkred" if "F" in labels[i][j] else "darkgreen",
                fontsize=11,
                fontweight="semibold",
            )

    ax.set_title(f"Confusion Matrix - {model_name}", fontsize=14, pad=12, fontweight="bold")
    ax.set_xlabel("Predicted Label", fontsize=12, labelpad=8)
    ax.set_ylabel("True Label", fontsize=12, labelpad=8)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Confusion matrix plot saved to: {output_path}")


def plot_roc_curves(roc_data: dict[str, tuple[np.ndarray, np.ndarray, float]],
                    output_path: Path) -> None:
    """
    Plots comparative ROC curves for multiple models with AUC values in legend.
    roc_data format: {model_name: (fpr, tpr, roc_auc)}
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 6), dpi=300)

    colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728"]
    for idx, (name, (fpr, tpr, auc_val)) in enumerate(roc_data.items()):
        color = colors[idx % len(colors)]
        ax.plot(
            fpr,
            tpr,
            label=f"{name} (AUC = {auc_val:.4f})",
            linewidth=2.2,
            color=color,
        )

    # Random chance line
    ax.plot([0, 1], [0, 1], "k--", label="Random Chance (AUC = 0.50)", linewidth=1.5, alpha=0.7)

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=12, labelpad=8)
    ax.set_ylabel("True Positive Rate (Recall / Sensitivity)", fontsize=12, labelpad=8)
    ax.set_title("Receiver Operating Characteristic (ROC) Curves", fontsize=14, pad=12, fontweight="bold")
    ax.legend(loc="lower right", fontsize=11, frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"ROC curve plot saved to: {output_path}")


def plot_feature_importance(feature_names: list[str], importances: np.ndarray,
                            model_name: str, output_path: Path, top_n: int = 12) -> None:
    """
    Plots horizontal bar chart of top N feature importances.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    feat_df = pd.DataFrame({
        "Feature": feature_names,
        "Importance": importances
    }).sort_values(by="Importance", ascending=True)

    if len(feat_df) > top_n:
        feat_df = feat_df.tail(top_n)

    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    bars = ax.barh(feat_df["Feature"], feat_df["Importance"], color="#2b5c8f", edgecolor="black", alpha=0.85)

    # Add data labels
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.005,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.4f}",
            ha="left",
            va="center",
            fontsize=10,
        )

    ax.set_title(f"Top {len(feat_df)} Feature Importances - {model_name}", fontsize=14, pad=12, fontweight="bold")
    ax.set_xlabel("Relative Importance Score", fontsize=12, labelpad=8)
    ax.set_ylabel("Engineered Feature", fontsize=12, labelpad=8)
    ax.grid(axis="x", linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Feature importance plot saved to: {output_path}")


def generate_eda_figures(df: pd.DataFrame, output_dir: Path) -> None:
    """
    Generates presentation-ready Exploratory Data Analysis figures.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Target Class Distribution
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    status_counts = df["Loan_Status"].value_counts()
    labels = ["Approved (Y)", "Rejected (N)"]
    vals = [status_counts.get(1, status_counts.get("Y", 0)),
            status_counts.get(0, status_counts.get("N", 0))]
    colors = ["#2ecc71", "#e74c3c"]
    bars = ax.bar(labels, vals, color=colors, edgecolor="black", width=0.55)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval + 5, f"{yval} ({yval/sum(vals)*100:.1f}%)",
                ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_title("Loan Approval Target Distribution", fontsize=13, fontweight="bold", pad=10)
    ax.set_ylabel("Applicant Count", fontsize=11)
    ax.set_ylim(0, max(vals) * 1.15)
    plt.tight_layout()
    plt.savefig(output_dir / "class_distribution.png", bbox_inches="tight")
    plt.close(fig)

    # 2. Correlation Heatmap for Numerical Features
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        fig, ax = plt.subplots(figsize=(9, 7), dpi=300)
        corr = df[num_cols].corr()
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, ax=ax, linewidths=0.5)
        ax.set_title("Correlation Heatmap (Numerical & Engineered Features)", fontsize=13, fontweight="bold", pad=10)
        plt.tight_layout()
        plt.savefig(output_dir / "correlation_heatmap.png", bbox_inches="tight")
        plt.close(fig)

    # 3. Credit History vs Loan Status
    if "Credit_History" in df.columns and "Loan_Status" in df.columns:
        fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
        crosstab = pd.crosstab(df["Credit_History"], df["Loan_Status"], normalize="index") * 100
        crosstab.plot(kind="bar", stacked=True, color=["#e74c3c", "#2ecc71"], ax=ax, edgecolor="black")
        ax.set_title("Credit History vs Loan Approval Rate (%)", fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("Credit History (0 = Bad / None, 1 = Good)", fontsize=11)
        ax.set_ylabel("Percentage (%)", fontsize=11)
        ax.set_xticklabels(["0.0 (Unfavorable)", "1.0 (Favorable)"], rotation=0)
        ax.legend(["Rejected", "Approved"], loc="upper left")
        plt.tight_layout()
        plt.savefig(output_dir / "credit_history_vs_status.png", bbox_inches="tight")
        plt.close(fig)
