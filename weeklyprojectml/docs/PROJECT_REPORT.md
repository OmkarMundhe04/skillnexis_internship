# Bank Loan Approval Prediction System
## Comprehensive Technical Project Report

**Author:** Omkar Mundhe  
**Email:** omkarmundhe04@gmail.com  
**Project Track:** Week 4 – Major Project / Machine Learning Capstone  
**Repository:** `OmkarMundhe04/skillnexis_internship/weeklyprojectml`  
**Date:** September 2026  

---

## 1. Abstract
The retail and commercial banking sectors are increasingly modernizing their loan underwriting procedures through automated decision-support systems. This project presents an end-to-end Machine Learning classification architecture engineered to predict personal loan approval outcomes based on borrower financial capacity, debt exposure, loan characteristics, and credit history. Using the Kaggle/Analytics Vidhya loan benchmark dataset of 614 applicant records, we developed a leakage-free preprocessing pipeline incorporating domain-specific feature engineering (Total Household Income, Equated Monthly Installment proxy, and Income-to-Loan ratios). Three diverse classification algorithms—Logistic Regression, Random Forest Classifier, and Extreme Gradient Boosting (XGBoost)—were trained on an 80% stratified split and evaluated on a 20% holdout test partition (123 samples). The champion model, **XGBoost**, achieved an overall **Accuracy of 85.37%**, **Precision of 83.84%**, **Recall of 97.65%**, **F1-Score of 0.9022**, and **ROC-AUC of 0.8563**. The pipeline is deployed via a multi-page interactive Streamlit web application enabling real-time risk scoring, probability visualization, and transparent risk factor breakdown.

---

## 2. Introduction
Credit assessment is fundamentally an exercise in risk management under uncertainty. Financial institutions must distinguish between solvent applicants capable of meeting debt amortization obligations and high-risk applicants prone to default. Historically, this evaluation relied on manual credit officer appraisals and rigid scorecard heuristics, which can be resource-intensive, slow, and susceptible to cognitive bias.

Supervised machine learning offers scalable, data-driven methodology to automate preliminary screening while preserving high predictive fidelity. However, deploying machine learning in financial contexts demands rigorous adherence to software engineering standards: strict prevention of data leakage, robust handling of missing data, interpretability of model decisions, and awareness of fair lending ethics. This capstone project demonstrates the complete end-to-end realization of these principles.

---

## 3. Problem Statement
Given an applicant's socio-demographic indicators, household earnings, requested loan specifications, and historical credit repayment status, design, train, and deploy an automated binary classification system to predict the likelihood of loan approval:

$$\hat{y} \in \{0, 1\} \quad \text{where } 1 = \text{Approved}, \ 0 = \text{Rejected}$$

The system must output well-calibrated class probabilities, identify primary explanatory drivers, operate via an intuitive web interface, and maintain complete reproducibility.

---

## 4. Objectives
1. **Data Preprocessing & Hygiene:** Detect and treat missing values, eliminate non-predictive identifiers, and enforce strict zero data leakage by isolating all transformers inside pipeline objects fitted only on training data.
2. **Domain-Specific Feature Engineering:** Formulate financial metrics reflecting true debt serviceability (e.g. household aggregate income, EMI burden proxy, debt-to-income ratio).
3. **Multi-Model Benchmarking:** Train and contrast a linear benchmark (Logistic Regression) against tree-based ensembles (Random Forest and XGBoost).
4. **Authentic Metric Evaluation:** Validate models on an independent stratified test split across Accuracy, Precision, Recall, F1-Score, and ROC-AUC metrics.
5. **Interactive Web Application:** Construct a production-grade Streamlit application featuring dedicated exploratory analysis, model diagnostic curves, and real-time applicant scoring.
6. **Documentation & Fair Lending Analysis:** Provide comprehensive technical reports, presentation materials, and ethical analyses addressing regulatory compliance and algorithmic bias.

---

## 5. Dataset Description
The model was trained on the standard benchmark Loan Prediction Dataset, consisting of 614 records and 13 variables:

| Column | Data Type | Role | Description |
| :--- | :--- | :--- | :--- |
| `Loan_ID` | String | Identifier | Unique application code (omitted from modeling) |
| `Gender` | String | Categorical | Applicant gender (`Male`, `Female`) |
| `Married` | String | Categorical | Marital status (`Yes`, `No`) |
| `Dependents` | String | Categorical | Number of financial dependents (`0`, `1`, `2`, `3+`) |
| `Education` | String | Categorical | Educational attainment (`Graduate`, `Not Graduate`) |
| `Self_Employed` | String | Categorical | Employment status (`Yes`, `No`) |
| `ApplicantIncome` | Integer | Numerical | Primary applicant gross monthly income |
| `CoapplicantIncome`| Float | Numerical | Co-applicant monthly income |
| `LoanAmount` | Float | Numerical | Requested loan amount in thousands ($K) |
| `Loan_Amount_Term`| Float | Numerical | Term of loan amortization in months (12 to 480) |
| `Credit_History` | Float | Numerical | Past credit repayment record (`1.0` = Good, `0.0` = Adverse) |
| `Property_Area` | String | Categorical | Collateral location (`Urban`, `Semiurban`, `Rural`) |
| **`Loan_Status`** | **String** | **Target** | **Approval outcome (`Y` = 1, `N` = 0)** |

### Target Distribution
- **Approved (`Y` / 1):** 422 records (68.73%)
- **Rejected (`N` / 0):** 192 records (31.27%)

---

## 6. Data Preprocessing
To guarantee zero data leakage, data cleaning and transformation procedures were strictly segregated:

1. **Initial Cleaning:**
   - Removal of arbitrary non-predictive identifiers (`Loan_ID`).
   - String stripping to remove trailing whitespace from categorical entries.
   - Validation that incomes and loan amounts are strictly non-negative.
2. **Leakage-Free Transformation Architecture:**
   - Numerical columns were processed through a sub-pipeline consisting of `SimpleImputer(strategy='median')` followed by `StandardScaler()`. The median was chosen due to positive skewness in financial values.
   - Categorical columns were processed via `SimpleImputer(strategy='most_frequent')` followed by `OneHotEncoder(handle_unknown='ignore', sparse_output=False)`.
   - The entire transformation is encapsulated inside scikit-learn's `ColumnTransformer`, which is fitted **exclusively on the training split**.

---

## 7. Exploratory Data Analysis (EDA)
Comprehensive exploratory analysis revealed several foundational credit insights:

1. **Credit History as Primary Predictor:**
   Applicants possessing a favorable credit record (`Credit_History = 1.0`) experienced an approval rate of **79.6%**. In contrast, applicants with adverse or unrecorded credit histories (`Credit_History = 0.0`) suffered a rejection rate of **91.8%**. This indicates that historical repayment behavior is the single most dominant linear discriminator.
2. **Income and Principal Collinearity:**
   A positive correlation of **0.62** was observed between `TotalIncome` and `LoanAmount`, confirming that applicants with higher income systematically apply for larger loan amounts.
3. **Property Area Divergence:**
   `Semiurban` property applications exhibited the highest relative approval rate (~76.8%), compared to `Urban` (~65.8%) and `Rural` (~61.4%).

---

## 8. Feature Engineering
Raw financial variables alone do not encapsulate repayment capacity. Four engineered features were derived:

1. **Total Household Income ($TotalIncome$):**
   $$TotalIncome = ApplicantIncome + CoapplicantIncome$$
   Reflects aggregate earning power available to service household obligations.
2. **Equated Monthly Installment Proxy ($EMI$):**
   $$EMI = \frac{LoanAmount \times 1000}{Loan\_Amount\_Term}$$
   Estimates the monthly debt service requirement.
3. **Income-to-Loan Ratio ($IncomeLoanRatio$):**
   $$IncomeLoanRatio = \frac{TotalIncome}{LoanAmount \times 1000}$$
   Measures borrower capacity relative to requested principal debt.
4. **Logarithmic Transforms ($Log\_TotalIncome$, $Log\_LoanAmount$):**
   Computed as $\ln(1 + x)$ to normalize heavy right-skewed currency distributions.

---

## 9. Machine Learning Models
Three distinct algorithmic paradigms were implemented and tuned:

1. **Logistic Regression (Baseline):**
   - Parametrization: $L_2$ penalty, `max_iter=1000`, `class_weight='balanced'`.
   - Purpose: Establishes a transparent linear decision boundary benchmark.
2. **Random Forest Classifier:**
   - Parametrization: `n_estimators=150`, `max_depth=5`, `min_samples_split=5`, `class_weight='balanced'`, `random_state=42`.
   - Purpose: Mitigates variance through bagging and captures non-linear feature interactions without overfitting.
3. **XGBoost Classifier:**
   - Parametrization: `n_estimators=100`, `max_depth=3`, `learning_rate=0.05`, `eval_metric='logloss'`, `random_state=42`.
   - Purpose: Sequentially optimizes pseudo-residuals via gradient boosted shallow decision trees.

---

## 10. Model Evaluation
The models were evaluated on the stratified holdout test split (123 records, 20% of total data). To ensure academic and industrial authenticity, metrics were computed from actual model execution:

- **Accuracy:** Overall correctness across all applicant classifications.
- **Precision:** $\frac{TP}{TP + FP}$ — proportion of predicted approvals that were truly creditworthy (protects the lender from loan defaults).
- **Recall (Sensitivity):** $\frac{TP}{TP + FN}$ — proportion of actual creditworthy applicants identified (protects underwriting volume and customer growth).
- **F1-Score:** $2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$ — harmonic mean balancing precision and recall.
- **ROC-AUC:** Area Under the Receiver Operating Characteristic Curve, evaluating ranking discrimination across all thresholds.

---

## 11. Results
The empirical evaluation results are summarized below:

| Model Architecture | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (Baseline)** | 83.74% | 87.36% | 89.41% | 0.8837 | 0.8601 |
| **Random Forest Classifier** | 84.55% | 89.29% | 88.24% | 0.8876 | **0.8659** |
| **XGBoost Classifier (Champion)** | **85.37%** | 83.84% | **97.65%** | **0.9022** | 0.8563 |

### Champion Model Selection
**XGBoost** was designated the champion model because it delivered the highest overall **F1-Score (0.9022)** and **Accuracy (85.37%)**, capturing **97.65%** of creditworthy applicants while maintaining a high **ROC-AUC of 0.8563**. For lenders prioritizing growth while strictly controlling default rates, this configuration provides superior operational utility.

---

## 12. Streamlit Application
An interactive web application was constructed using Streamlit (`app.py`), organized into five functional tabs:
1. **🏠 Home:** Project overview, problem definition, interactive workflow diagram, and regulatory disclaimers.
2. **📊 Dataset & EDA:** Interactive raw data preview, column definitions, class balance distribution, credit history cross-tabulations, and correlation heatmaps.
3. **🤖 Model Performance:** Champion model metric cards, full comparison table, confusion matrix, comparative ROC curves, and feature importance bar plots.
4. **🔮 Loan Prediction:** Interactive form with client validation allowing users to test custom applicant profiles and view real-time approval/rejection likelihoods, risk tiers, and calculated financial ratios.
5. **ℹ️ About:** Technical stack summary, author credentials, project repository links, and ethical AI guidelines.

---

## 13. Limitations
1. **Sample Volume:** With 614 total records, the dataset is relatively small, which can lead to variance in estimation for rare demographic combinations.
2. **Binary Credit Representation:** Real financial institutions operate with continuous bureau scores (e.g. FICO 300–850) rather than a binary 0/1 credit history flag.
3. **Absence of Macroeconomic Factors:** Prevailing interest rates, regional inflation, and economic cycle indicators are not captured in the historical dataset.

---

## 14. Ethical Considerations & Fair Lending
Deploying machine learning models in credit underwriting introduces significant legal and ethical responsibilities:
- **Fair Lending Compliance:** Statutes such as the US Equal Credit Opportunity Act (ECOA) prohibit credit discrimination based on protected characteristics (Gender, Marital Status). Although present in benchmark datasets, these features should be audited and excluded from real production scorecards.
- **Disparate Impact:** Algorithms can inadvertently learn proxy correlations that disproportionately disadvantage protected demographic groups. Regular bias audits (disparate impact ratio tests) are essential.
- **Adverse Action Transparency:** Applicants denied credit possess a legal right to receive specific reasons. Models must be supported by transparent feature attribution techniques (e.g., SHAP).
- **Human-in-the-Loop:** Algorithmic scoring must remain a consultative screening tool; human credit officers must retain ultimate approval authority.

---

## 15. Future Scope
1. **Explainable AI (XAI) Integration:** Incorporate interactive SHAP (SHapley Additive exPlanations) force plots and waterfall charts directly inside the Streamlit user interface.
2. **Continuous Bureau Modeling:** Expand the pipeline to handle continuous credit scores, debt-to-income (DTI) ceilings, and loan-to-value (LTV) limits.
3. **Automated Retraining CI/CD:** Establish automated drift monitoring pipelines to detect covariate shift in applicant populations over time.

---

## 16. Conclusion
The Bank Loan Approval Prediction System fulfills all technical and academic objectives of an applied machine learning capstone project. By adhering to strict leakage-free preprocessing, deriving domain-grounded financial features, conducting rigorous multi-model benchmarking, and deploying a responsive Streamlit application, the project delivers a complete, professional, and presentation-ready data science solution.
