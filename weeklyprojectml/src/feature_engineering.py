"""
Feature Engineering Module for Bank Loan Approval Prediction.
Derives domain-relevant banking features:
1. TotalIncome: Combined household earning power (ApplicantIncome + CoapplicantIncome)
2. EMI: Approximate monthly repayment burden ((LoanAmount * 1000) / Loan_Amount_Term)
3. IncomeLoanRatio: Applicant's financial capacity vs debt obligation
4. Log Transformations: Stabilizes skewness in heavy-tailed financial distributions
"""

import numpy as np
import pandas as pd


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes derived financial ratios and log transformations on the dataset.
    Safely handles division by zero and missing values.
    """
    df_feat = df.copy()

    # 1. Total Household Income
    applicant_income = df_feat.get("ApplicantIncome", 0).fillna(0)
    coapplicant_income = df_feat.get("CoapplicantIncome", 0).fillna(0)
    df_feat["TotalIncome"] = applicant_income + coapplicant_income

    # 2. Approximate Monthly EMI
    # Note: LoanAmount in this standard dataset is expressed in thousands ($K)
    # Loan_Amount_Term is expressed in months (e.g. 360 = 30 years)
    loan_amt = df_feat.get("LoanAmount", np.nan)
    loan_term = df_feat.get("Loan_Amount_Term", np.nan)

    # Safe EMI calculation
    df_feat["EMI"] = np.where(
        pd.notnull(loan_amt) & pd.notnull(loan_term) & (loan_term > 0),
        (loan_amt * 1000.0) / loan_term,
        np.nan,
    )

    # 3. Income to Loan Ratio (Debt service capability)
    # Total annual/monthly income divided by requested principal
    df_feat["IncomeLoanRatio"] = np.where(
        pd.notnull(loan_amt) & (loan_amt > 0),
        df_feat["TotalIncome"] / (loan_amt * 1000.0),
        np.nan,
    )

    # 4. Log Transformations for skewed distributions
    # Using np.log1p to handle 0 income safely
    df_feat["Log_TotalIncome"] = np.log1p(np.maximum(df_feat["TotalIncome"], 0))
    df_feat["Log_LoanAmount"] = np.where(
        pd.notnull(loan_amt) & (loan_amt > 0),
        np.log1p(loan_amt),
        np.nan,
    )

    return df_feat
