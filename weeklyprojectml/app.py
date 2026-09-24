"""
Bank Loan Approval Prediction System - Streamlit Web Application.
Multi-page interactive application for educational loan evaluation,
exploratory data analysis, model comparison, and real-time inference.
"""

import json
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
from PIL import Image

from src.predict import load_pipeline, predict_loan

# Directories
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
METRICS_PATH = OUTPUTS_DIR / "metrics" / "model_metrics.json"

# Page Configuration
st.set_page_config(
    page_title="Bank Loan Approval Prediction System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4b5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-title {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
    }
    .decision-approved {
        background: #ecfdf5;
        border: 2px solid #10b981;
        border-radius: 12px;
        padding: 1.5rem;
        color: #065f46;
        margin-top: 1rem;
    }
    .decision-rejected {
        background: #fef2f2;
        border: 2px solid #ef4444;
        border-radius: 12px;
        padding: 1.5rem;
        color: #991b1b;
        margin-top: 1rem;
    }
    .disclaimer-box {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 0.8rem 1rem;
        border-radius: 4px;
        color: #92400e;
        font-size: 0.9rem;
        margin-top: 1rem;
    }
    .flowchart-step {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 0.6rem;
        text-align: center;
        font-weight: 600;
        color: #334155;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_cached_pipeline():
    """Loads and caches the model pipeline."""
    try:
        return load_pipeline()
    except Exception as exc:
        return None


@st.cache_data
def load_metrics_data():
    """Reads saved model metrics JSON."""
    if METRICS_PATH.exists():
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


@st.cache_data
def load_raw_preview():
    """Loads raw dataset preview."""
    csv_path = DATA_DIR / "raw" / "loan_prediction.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return None


# Sidebar Navigation
st.sidebar.image(
    "https://img.icons8.com/isometric/100/bank-building.png",
    width=70,
)
st.sidebar.title("Loan Approval ML")
st.sidebar.markdown("**Capstone Project** • *Python ML*")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation Menu",
    [
        "🏠 Home",
        "📊 Dataset & EDA",
        "🤖 Model Performance",
        "🔮 Loan Prediction",
        "ℹ️ About",
    ],
)

st.sidebar.divider()
st.sidebar.caption("👨‍💻 Developed by **Omkar Mundhe**")
st.sidebar.caption("📧 omkarmundhe04@gmail.com")

pipeline = get_cached_pipeline()
metrics_data = load_metrics_data()


# ==========================================
# PAGE 1: HOME
# ==========================================
if page == "🏠 Home":
    st.markdown('<div class="main-header">🏦 Bank Loan Approval Prediction</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">An Educational Machine Learning System for Risk Assessment & Automated Classification</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### Executive Overview
        In retail and commercial banking, assessing personal creditworthiness requires balancing risk mitigation 
        with efficient customer onboarding. This project demonstrates an end-to-end **Machine Learning Classification System** 
        trained on historical loan application outcomes to estimate loan approval probabilities.
        
        The predictive pipeline ingests applicant demographic details, employment profile, debt burden, and historical credit 
        record, applies leakage-free preprocessing, derives domain-specific financial features, and evaluates applications 
        via high-performance supervised classifiers.
        """
    )

    st.divider()

    st.subheader("🔄 Machine Learning Workflow")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown('<div class="flowchart-step">1. Applicant Data<br><small>Demographics & Financials</small></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="flowchart-step">2. Preprocessing<br><small>Imputation & Scaling</small></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="flowchart-step">3. Feature Eng.<br><small>Income/Loan & EMI Ratios</small></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="flowchart-step">4. ML Classifiers<br><small>Logistic, RF & XGBoost</small></div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="flowchart-step">5. Decision Engine<br><small>Probability & Risk Tier</small></div>', unsafe_allow_html=True)

    st.divider()

    st.subheader("Key Capabilities")
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        st.markdown("#### 🛡️ Leakage-Free Preprocessing")
        st.write("All transformations (imputations, scalers, encoders) are fitted strictly on training splits within scikit-learn pipelines.")
    with fcol2:
        st.markdown("#### 📈 Multi-Model Comparison")
        st.write("Evaluates Logistic Regression baseline against Random Forest and XGBoost using ROC-AUC, F1-Score, and confusion matrices.")
    with fcol3:
        st.markdown("#### ⚡ Real-Time Probability Scoring")
        st.write("Provides transparent approval and rejection likelihoods accompanied by primary explanatory risk factors.")

    st.markdown(
        """
        <div class="disclaimer-box">
            <strong>⚠️ Educational Notice & Disclaimer:</strong><br>
            This software is an educational machine learning demonstration built for an academic internship portfolio. 
            All inferences generated are statistical estimates and must <strong>NEVER</strong> be utilized as actual banking, legal, 
            or underwriting lending decisions.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# PAGE 2: DATASET & EDA
# ==========================================
elif page == "📊 Dataset & EDA":
    st.markdown('<div class="main-header">📊 Dataset & Exploratory Data Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Data hygiene, distribution analysis, and structural insights from the benchmark dataset</div>',
        unsafe_allow_html=True,
    )

    df_preview = load_raw_preview()
    if df_preview is not None:
        st.subheader("📋 Dataset Preview & Attributes")
        st.write(f"Total Records: **{df_preview.shape[0]}** | Attributes: **{df_preview.shape[1]}**")
        st.dataframe(df_preview.head(5), use_container_width=True)

        with st.expander("🔍 View Dataset Column Definitions"):
            st.markdown(
                """
                - **Loan_ID**: Unique identification code for each loan application
                - **Gender**: Gender of the primary applicant (`Male` / `Female`)
                - **Married**: Marital status (`Yes` / `No`)
                - **Dependents**: Number of financial dependents (`0`, `1`, `2`, `3+`)
                - **Education**: Educational attainment (`Graduate` / `Not Graduate`)
                - **Self_Employed**: Self-employment status (`Yes` / `No`)
                - **ApplicantIncome**: Monthly earnings of the primary applicant
                - **CoapplicantIncome**: Monthly earnings of the co-applicant
                - **LoanAmount**: Requested principal loan amount (in thousands of rupees / ₹)
                - **Loan_Amount_Term**: Repayment duration in months (e.g. 360 months = 30 years)
                - **Credit_History**: Past credit repayment record (`1.0` = Meets guidelines, `0.0` = Adverse/None)
                - **Property_Area**: Geographic category of the collateral property (`Urban`, `Semiurban`, `Rural`)
                - **Loan_Status**: Binary target outcome (`Y` = Approved, `N` = Rejected)
                """
            )
    else:
        st.warning("Raw dataset file not found in `data/raw/loan_prediction.csv`.")

    st.divider()

    st.subheader("📈 Statistical Visualizations & Key Findings")

    eda_col1, eda_col2 = st.columns(2)
    with eda_col1:
        st.markdown("#### 1. Target Class Distribution")
        target_fig = FIGURES_DIR / "class_distribution.png"
        if target_fig.exists():
            st.image(str(target_fig), use_container_width=True)
            st.caption(
                "**Observation**: The dataset exhibits a moderate class balance with ~68.7% approved (Y) "
                "and ~31.3% rejected (N). Stratified sampling was applied during train/test splitting "
                "to maintain identical class ratios in validation."
            )
        else:
            st.info("Class distribution plot will be available after running training.")

    with eda_col2:
        st.markdown("#### 2. Credit History Impact")
        credit_fig = FIGURES_DIR / "credit_history_vs_status.png"
        if credit_fig.exists():
            st.image(str(credit_fig), use_container_width=True)
            st.caption(
                "**Observation**: Applicants with a favorable credit history (`1.0`) achieve an approval rate "
                "exceeding 79%, whereas applicants with adverse/unrecorded credit history (`0.0`) experience "
                "rejection rates over 90%. Credit history is the dominant single predictive indicator."
            )
        else:
            st.info("Credit history plot will be available after running training.")

    st.divider()

    st.markdown("#### 3. Correlation Heatmap")
    heatmap_fig = FIGURES_DIR / "correlation_heatmap.png"
    if heatmap_fig.exists():
        st.image(str(heatmap_fig), use_container_width=True)
        st.caption(
            "**Observation**: A notable positive correlation (~0.62) exists between `TotalIncome` and `LoanAmount`. "
            "Engineered features like `IncomeLoanRatio` and `EMI` effectively capture applicant repayment capacity "
            "rather than absolute income scale alone."
        )


# ==========================================
# PAGE 3: MODEL PERFORMANCE
# ==========================================
elif page == "🤖 Model Performance":
    st.markdown('<div class="main-header">🤖 Model Comparison & Evaluation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Comprehensive comparative analysis of baseline and ensemble classifiers</div>',
        unsafe_allow_html=True,
    )

    if metrics_data and "models" in metrics_data:
        best_name = metrics_data.get("best_model", "XGBoost")
        models_dict = metrics_data["models"]

        st.subheader(f"🏆 Champion Model: {best_name}")
        best_metrics = models_dict.get(best_name, {})

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Accuracy</div><div class="metric-val">{best_metrics.get("accuracy", 0):.2%}</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Precision</div><div class="metric-val">{best_metrics.get("precision", 0):.2%}</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Recall</div><div class="metric-val">{best_metrics.get("recall", 0):.2%}</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="metric-card"><div class="metric-title">F1-Score</div><div class="metric-val">{best_metrics.get("f1_score", 0):.4f}</div></div>', unsafe_allow_html=True)
        with m5:
            st.markdown(f'<div class="metric-card"><div class="metric-title">ROC-AUC</div><div class="metric-val">{best_metrics.get("roc_auc", 0):.4f}</div></div>', unsafe_allow_html=True)

        st.caption(f"*{metrics_data.get('selection_criteria', '')}*")

        st.divider()

        st.subheader("📊 Model Comparison Table")
        comparison_rows = []
        for name, m in models_dict.items():
            comparison_rows.append({
                "Model Name": name,
                "Accuracy": f"{m.get('accuracy', 0):.4f}",
                "Precision": f"{m.get('precision', 0):.4f}",
                "Recall": f"{m.get('recall', 0):.4f}",
                "F1-Score": f"{m.get('f1_score', 0):.4f}",
                "ROC-AUC": f"{m.get('roc_auc', 0):.4f}",
            })
        st.table(pd.DataFrame(comparison_rows))

        with st.expander("💡 Metric Explanations"):
            st.markdown(
                """
                - **Accuracy**: Percentage of correct overall loan decisions (both approvals and rejections).
                - **Precision**: Out of all predicted approvals, what percentage was truly creditworthy (minimizes false approvals / defaults).
                - **Recall (Sensitivity)**: Out of all truly creditworthy applicants, what percentage was identified by the model.
                - **F1-Score**: Harmonic mean of Precision and Recall, providing a robust balance for moderately imbalanced credit data.
                - **ROC-AUC**: Measures the model's ability to rank risk probabilities across all possible decision thresholds regardless of cutoff.
                """
            )

        st.divider()

        st.subheader("📈 Diagnostic Curves & Interpretability")
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.markdown("#### Confusion Matrix (Holdout Test Split)")
            cm_fig = FIGURES_DIR / "confusion_matrix.png"
            if cm_fig.exists():
                st.image(str(cm_fig), use_container_width=True)
            else:
                st.info("Confusion matrix figure not found.")

        with d_col2:
            st.markdown("#### Comparative ROC Curves")
            roc_fig = FIGURES_DIR / "roc_curve.png"
            if roc_fig.exists():
                st.image(str(roc_fig), use_container_width=True)
            else:
                st.info("ROC curve figure not found.")

        st.markdown("#### Feature Importance Analysis")
        feat_fig = FIGURES_DIR / "feature_importance.png"
        if feat_fig.exists():
            st.image(str(feat_fig), use_container_width=True)
            st.caption(
                "**Important Note on Interpretability**: Feature importance indicates the relative contribution "
                "of features to the tree split decisions. It denotes **model influence**, not direct real-world causal determination."
            )
    else:
        st.info("Metrics not found. Please run `python src/train.py` to evaluate models.")


# ==========================================
# PAGE 4: PREDICTION
# ==========================================
elif page == "🔮 Loan Prediction":
    st.markdown('<div class="main-header">🔮 Interactive Loan Approval Prediction</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Enter prospective applicant parameters to evaluate real-time approval probability</div>',
        unsafe_allow_html=True,
    )

    if pipeline is None:
        st.error(
            "⚠️ Trained model artifact not found! Please run `python src/train.py` from the project directory."
        )
    else:
        with st.form("loan_prediction_form"):
            st.markdown("#### 1. Demographic & Personal Background")
            c1, c2, c3 = st.columns(3)
            with c1:
                gender = st.selectbox("Gender", ["Male", "Female"])
            with c2:
                married = st.selectbox("Marital Status", ["Yes", "No"], index=0)
            with c3:
                dependents = st.selectbox("Dependents", ["0", "1", "2", "3+"], index=0)

            c4, c5 = st.columns(2)
            with c4:
                education = st.selectbox("Education Level", ["Graduate", "Not Graduate"], index=0)
            with c5:
                self_employed = st.selectbox("Self Employed?", ["No", "Yes"], index=0)

            st.markdown("#### 2. Financial & Income Information")
            f1, f2 = st.columns(2)
            with f1:
                applicant_income = st.number_input(
                    "Primary Applicant Monthly Income (₹)",
                    min_value=0,
                    max_value=1500000,
                    value=50000,
                    step=2500,
                    help="Gross monthly earnings before deductions in Indian Rupees",
                )
            with f2:
                coapplicant_income = st.number_input(
                    "Co-Applicant Monthly Income (₹)",
                    min_value=0,
                    max_value=1000000,
                    value=18000,
                    step=2500,
                    help="Monthly income of co-signer or guarantor in Indian Rupees",
                )

            st.markdown("#### 3. Loan Requirements & Credit Profile")
            l1, l2, l3 = st.columns(3)
            with l1:
                loan_amount = st.number_input(
                    "Loan Amount Requested (in Thousands ₹)",
                    min_value=5,
                    max_value=5000,
                    value=130,
                    step=5,
                    help="e.g. 130 represents ₹1,30,000 (1.3 Lakhs)",
                )
            with l2:
                loan_term = st.selectbox(
                    "Repayment Term (Months)",
                    [12, 36, 60, 84, 120, 180, 240, 300, 360, 480],
                    index=8,  # Default 360 (30 years)
                    help="Duration of the loan amortization in months",
                )
            with l3:
                property_area = st.selectbox(
                    "Collateral Property Area",
                    ["Semiurban", "Urban", "Rural"],
                    index=0,
                )

            st.markdown("#### 4. Historical Credit Record")
            credit_choice = st.radio(
                "Past Credit History Guidelines",
                options=[
                    "Meets Standard Credit Guidelines (1.0 - Good History)",
                    "Does NOT Meet Guidelines / Adverse Past Defaults (0.0 - Bad History)",
                ],
                index=0,
                horizontal=True,
            )
            credit_history = 1.0 if "1.0" in credit_choice else 0.0

            submit_btn = st.form_submit_button(
                "🚀 Predict Loan Approval",
                use_container_width=True,
            )

        if submit_btn:
            applicant_input = {
                "Gender": gender,
                "Married": married,
                "Dependents": dependents,
                "Education": education,
                "Self_Employed": self_employed,
                "ApplicantIncome": float(applicant_income),
                "CoapplicantIncome": float(coapplicant_income),
                "LoanAmount": float(loan_amount),
                "Loan_Amount_Term": float(loan_term),
                "Credit_History": float(credit_history),
                "Property_Area": property_area,
            }

            with st.spinner("Processing application through ML pipeline..."):
                try:
                    result = predict_loan(applicant_input, pipeline=pipeline)

                    is_approved = result["prediction"] == 1
                    app_prob = result["approval_probability"]
                    rej_prob = result["rejection_probability"]
                    risk_lvl = result["risk_level"]

                    st.divider()
                    st.subheader("Assessment Results")

                    if is_approved:
                        st.markdown(
                            f"""
                            <div class="decision-approved">
                                <h3 style="margin-top:0;">✅ Prediction: Likely Approved</h3>
                                <p style="font-size:1.1rem; margin-bottom:0.5rem;">
                                    The machine learning model predicts that this loan application is <strong>likely to be approved</strong>.
                                </p>
                                <strong>Assessed Risk Profile:</strong> {risk_lvl}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"""
                            <div class="decision-rejected">
                                <h3 style="margin-top:0;">❌ Prediction: Likely Not Approved</h3>
                                <p style="font-size:1.1rem; margin-bottom:0.5rem;">
                                    The machine learning model predicts that this loan application is <strong>likely to be rejected</strong>.
                                </p>
                                <strong>Assessed Risk Profile:</strong> {risk_lvl}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # Probability Bars
                    p_col1, p_col2 = st.columns(2)
                    with p_col1:
                        st.metric("Approval Probability", f"{app_prob:.1f}%")
                        st.progress(app_prob / 100.0)
                    with p_col2:
                        st.metric("Rejection Probability", f"{rej_prob:.1f}%")
                        st.progress(rej_prob / 100.0)

                    # Key Indicators Breakdown
                    st.markdown("#### Primary Explanatory Factors")
                    for factor in result["key_factors"]:
                        st.markdown(f"- 📌 {factor}")

                    # Derived Financial Ratios
                    total_inc = applicant_income + coapplicant_income
                    emi_val = (loan_amount * 1000.0) / loan_term if loan_term > 0 else 0
                    dti_ratio = (emi_val / total_inc * 100) if total_inc > 0 else 0

                    with st.expander("📊 Calculated Financial Indicators"):
                        st.write(f"- **Combined Monthly Household Income**: ₹{total_inc:,.2f}")
                        st.write(f"- **Approximate Monthly EMI**: ₹{emi_val:,.2f}")
                        st.write(f"- **Estimated Monthly Debt Burden (EMI / Income)**: {dti_ratio:.1f}%")

                    st.markdown(
                        f"""
                        <div class="disclaimer-box">
                            <strong>Disclaimer:</strong> {result["disclaimer"]}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                except Exception as exc:
                    st.error(f"Prediction error occurred: {exc}")


# ==========================================
# PAGE 5: ABOUT
# ==========================================
elif page == "ℹ️ About":
    st.markdown('<div class="main-header">ℹ️ About the Project</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Internship Capstone Project • Architecture, Tech Stack & Ethical Principles</div>',
        unsafe_allow_html=True,
    )

    t1, t2 = st.columns([2, 1])
    with t1:
        st.markdown(
            """
            ### Project Description
            The **Bank Loan Approval Prediction System** is an educational capstone project developed 
            to showcase practical machine learning engineering, data preprocessing hygiene, feature engineering, 
            rigorous cross-model evaluation, and clean web deployment.

            ### Technologies Used
            - **Programming Language**: Python 3.13
            - **Data Manipulation**: pandas, NumPy
            - **Machine Learning**: scikit-learn, XGBoost
            - **Visualization**: Matplotlib, Seaborn
            - **Web Application Framework**: Streamlit
            - **Model Serialization**: joblib
            """
        )

        st.markdown(
            """
            ### Evaluated Machine Learning Models
            1. **Logistic Regression**: Serves as a standard, highly interpretable baseline with balanced class weights.
            2. **Random Forest Classifier**: Ensemble of bagged decision trees capturing non-linear interactions.
            3. **XGBoost Classifier**: Extreme Gradient Boosting providing high predictive power and handling gradient descent optimization.
            """
        )

    with t2:
        st.markdown(
            """
            ### Author Information
            - **Developer**: Omkar Mundhe
            - **Email**: omkarmundhe04@gmail.com
            - **Role**: Machine Learning Intern
            - **Track**: Python & Applied ML Capstone
            - **License**: MIT Open Source License
            """
        )

    st.divider()

    st.subheader("⚖️ Ethical Considerations & Fair Lending Principles")
    st.markdown(
        """
        Building machine learning models for financial decision-making requires active awareness of ethical risks:
        
        1. **Sensitive Attributes & Proxy Discrimination**: The dataset includes demographic attributes such as `Gender` and `Married`. 
           In real-world credit models, regulations (e.g., the US Equal Credit Opportunity Act - ECOA) explicitly prohibit lending decisions based on 
           gender, marital status, or protected characteristics. Even when explicit attributes are excluded, correlated proxy variables can introduce indirect bias.
        2. **Historical Data Bias**: Models learn patterns present in historical training records. If historical lending decisions reflected socio-economic biases 
           against certain demographics, the algorithm risks perpetuating those inequities.
        3. **Explainability & Adverse Action Notices**: Financial regulations require lenders to provide applicants with specific, understandable reasons 
           whenever credit is denied (Adverse Action Notice). Black-box models must be accompanied by explainability frameworks (e.g., SHAP, LIME, or transparent scorecards).
        4. **Human-in-the-Loop Oversight**: Algorithmic predictions should only serve as decision-support recommendations. Final credit allocation must remain 
           subject to accredited human underwriting review.
        """
    )
