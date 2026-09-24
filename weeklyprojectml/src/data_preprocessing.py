"""
Data Preprocessing Module for Bank Loan Approval Prediction.
Handles data loading, validation, cleaning, and preparation of scikit-learn
ColumnTransformers to guarantee zero data leakage between train and test splits.
"""

from pathlib import Path
import urllib.request
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RAW_DATA_URL = (
    "https://raw.githubusercontent.com/shrikant-temburwar/"
    "Loan-Prediction-Dataset/master/train.csv"
)

# Standard categorical and numerical columns in the loan dataset
CATEGORICAL_COLS = [
    "Gender",
    "Married",
    "Dependents",
    "Education",
    "Self_Employed",
    "Property_Area",
]

NUMERICAL_COLS = [
    "ApplicantIncome",
    "CoapplicantIncome",
    "LoanAmount",
    "Loan_Amount_Term",
    "Credit_History",
    "TotalIncome",
    "IncomeLoanRatio",
    "EMI",
    "Log_TotalIncome",
    "Log_LoanAmount",
]


def get_data_dir() -> Path:
    """Returns the base data directory relative to project root."""
    return Path(__file__).resolve().parent.parent / "data"


def ensure_dataset(data_path: Path | None = None) -> Path:
    """
    Ensures that the raw loan prediction dataset exists locally.
    Downloads the standard benchmark dataset if not found.
    """
    if data_path is None:
        data_path = get_data_dir() / "raw" / "loan_prediction.csv"

    data_path.parent.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        print(f"Downloading raw dataset from {RAW_DATA_URL}...")
        try:
            req = urllib.request.Request(
                RAW_DATA_URL,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req) as response, open(data_path, "wb") as out_file:
                out_file.write(response.read())
            print(f"Dataset successfully saved to: {data_path}")
        except Exception as exc:
            raise RuntimeError(
                f"Failed to automatically download dataset: {exc}. "
                f"Please manually place 'loan_prediction.csv' in '{data_path.parent}'."
            ) from exc

    return data_path


def load_raw_data(data_path: Path | None = None) -> pd.DataFrame:
    """Loads raw loan dataset into a pandas DataFrame."""
    resolved_path = ensure_dataset(data_path)
    df = pd.read_csv(resolved_path)
    return df


def clean_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs initial data hygiene:
    - Removes duplicate records
    - Standardizes text whitespace
    - Handles invalid / anomalous values (e.g. negative income, zero loan amounts)
    - Drops non-predictive identifiers like Loan_ID
    - Encodes Loan_Status target variable ('Y' -> 1, 'N' -> 0)
    """
    df_cleaned = df.copy()

    # Drop duplicates if present
    df_cleaned = df_cleaned.drop_duplicates()

    # Clean whitespace in string columns
    str_cols = df_cleaned.select_dtypes(include="object").columns
    for col in str_cols:
        df_cleaned[col] = df_cleaned[col].astype(str).str.strip()
        # Replace string 'nan' with actual NaN
        df_cleaned[col] = df_cleaned[col].replace({"nan": np.nan, "None": np.nan})

    # Drop Loan_ID if present
    if "Loan_ID" in df_cleaned.columns:
        df_cleaned = df_cleaned.drop(columns=["Loan_ID"])

    # Sanitize invalid numerical numbers
    if "ApplicantIncome" in df_cleaned.columns:
        df_cleaned["ApplicantIncome"] = df_cleaned["ApplicantIncome"].apply(
            lambda x: np.nan if pd.notnull(x) and x < 0 else x
        )

    if "CoapplicantIncome" in df_cleaned.columns:
        df_cleaned["CoapplicantIncome"] = df_cleaned["CoapplicantIncome"].apply(
            lambda x: np.nan if pd.notnull(x) and x < 0 else x
        )

    if "LoanAmount" in df_cleaned.columns:
        df_cleaned["LoanAmount"] = df_cleaned["LoanAmount"].apply(
            lambda x: np.nan if pd.notnull(x) and x <= 0 else x
        )

    # Encode target variable
    if "Loan_Status" in df_cleaned.columns:
        target_map = {"Y": 1, "N": 0, "1": 1, "0": 0, 1: 1, 0: 0}
        df_cleaned["Loan_Status"] = df_cleaned["Loan_Status"].map(target_map)

    return df_cleaned


def build_preprocessor(categorical_features: list[str] | None = None,
                       numerical_features: list[str] | None = None) -> ColumnTransformer:
    """
    Constructs a scikit-learn ColumnTransformer.
    - Numerical: Median imputation -> StandardScaler
    - Categorical: Most Frequent imputation -> OneHotEncoder(handle_unknown='ignore')
    This pipeline object will be fitted ONLY on training split to prevent leakage.
    """
    cat_cols = categorical_features or CATEGORICAL_COLS
    num_cols = numerical_features or NUMERICAL_COLS

    numerical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numerical_pipeline, num_cols),
            ("cat", categorical_pipeline, cat_cols),
        ],
        remainder="drop",
    )

    return preprocessor
