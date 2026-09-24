"""
Inference Smoke Tests across multiple applicant scenarios.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.predict import predict_loan


def run_tests():
    test_cases = [
        {
            "name": "Case 1: Standard Applicant (Good Credit, Moderate Income)",
            "data": {
                "Gender": "Male",
                "Married": "Yes",
                "Dependents": "1",
                "Education": "Graduate",
                "Self_Employed": "No",
                "ApplicantIncome": 5500,
                "CoapplicantIncome": 2200,
                "LoanAmount": 130,
                "Loan_Amount_Term": 360,
                "Credit_History": 1.0,
                "Property_Area": "Semiurban",
            },
        },
        {
            "name": "Case 2: High Debt Burden / Disproportionate Loan",
            "data": {
                "Gender": "Female",
                "Married": "No",
                "Dependents": "2",
                "Education": "Not Graduate",
                "Self_Employed": "Yes",
                "ApplicantIncome": 1200,
                "CoapplicantIncome": 0,
                "LoanAmount": 450,
                "Loan_Amount_Term": 180,
                "Credit_History": 1.0,
                "Property_Area": "Rural",
            },
        },
        {
            "name": "Case 3: Adverse / Zero Credit History",
            "data": {
                "Gender": "Male",
                "Married": "Yes",
                "Dependents": "0",
                "Education": "Graduate",
                "Self_Employed": "No",
                "ApplicantIncome": 8000,
                "CoapplicantIncome": 3000,
                "LoanAmount": 150,
                "Loan_Amount_Term": 360,
                "Credit_History": 0.0,
                "Property_Area": "Urban",
            },
        },
    ]

    for tc in test_cases:
        print("=" * 60)
        print(tc["name"])
        res = predict_loan(tc["data"])
        pred_label = res["prediction_label"]
        app_prob = res["approval_probability"]
        rej_prob = res["rejection_probability"]
        risk = res["risk_level"]
        print(f"Prediction: {pred_label} (Approval: {app_prob}%, Rejection: {rej_prob}%)")
        print(f"Risk Level: {risk}")
        for factor in res["key_factors"]:
            print(f" - {factor}")


if __name__ == "__main__":
    run_tests()
