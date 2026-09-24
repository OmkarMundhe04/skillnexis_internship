"""
Titanic Survival Prediction – Data Cleaning Project
Mini Project 1: Internship Submission

This script performs end-to-end data cleaning, preprocessing, 
feature encoding, exploratory visualization, and export of the Titanic dataset.

Tasks Completed:
1. Handling Missing Data (Age, Embarked, Cabin)
2. Encoding Categorical Features ('Sex', 'Embarked')
3. Visualizing Age Distribution (Matplotlib with Seaborn styling)
4. Exporting the Cleaned Dataset to CSV ('titanic_cleaned.csv')
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

def run_data_cleaning_pipeline(input_csv='Titanic-Dataset.csv', output_csv='titanic_cleaned.csv'):
    print("=" * 70)
    print("TITANIC DATA CLEANING & PREPROCESSING PIPELINE")
    print("=" * 70)
    
    # -------------------------------------------------------------
    # Step 1: Load the Dataset
    # -------------------------------------------------------------
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Dataset '{input_csv}' not found in current directory.")
        
    df = pd.read_csv(input_csv)
    print(f"\n[+] Dataset loaded successfully from '{input_csv}'")
    print(f"    - Total Rows: {df.shape[0]}")
    print(f"    - Total Columns: {df.shape[1]}")
    print(f"    - Columns: {list(df.columns)}")
    
    # Store original Age for comparison plotting later
    df['Age_Original'] = df['Age'].copy()
    
    # -------------------------------------------------------------
    # Step 2: Missing Data Analysis
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("STEP 1: MISSING VALUE ANALYSIS & CLEANING")
    print("-" * 70)
    missing_before = df.isnull().sum()
    missing_percent = (missing_before / len(df)) * 100
    missing_df = pd.DataFrame({'Missing_Count': missing_before, 'Percentage (%)': missing_percent})
    print("Missing values in raw data:")
    print(missing_df[missing_df['Missing_Count'] > 0])
    
    # 1. Clean 'Embarked' (2 missing values)
    # The most frequent port of embarkation is 'S' (Southampton) with >70% of passengers.
    embarked_mode = df['Embarked'].mode()[0]
    df['Embarked'] = df['Embarked'].fillna(embarked_mode)
    print(f"\n[OK] Cleaned 'Embarked': Imputed 2 missing values with mode ('{embarked_mode}').")
    
    # 2. Clean 'Age' (177 missing values)
    # Domain-aware median imputation based on Passenger Class and Gender
    # This prevents distribution distortion and retains age differences across classes.
    class_sex_medians = df.groupby(['Pclass', 'Sex'])['Age'].median()
    print("\nMedian Age by (Pclass, Sex) groups used for imputation:")
    print(class_sex_medians)
    
    df['Age'] = df.groupby(['Pclass', 'Sex'])['Age'].transform(lambda x: x.fillna(x.median()))
    # In case any group was completely empty, fallback to overall median
    if df['Age'].isnull().sum() > 0:
        df['Age'] = df['Age'].fillna(df['Age'].median())
    df['Age'] = df['Age'].round(1)
    print(f"[OK] Cleaned 'Age': Imputed 177 missing values using grouped medians by (Pclass, Sex).")
    
    # 3. Clean 'Cabin' (687 missing values, ~77.1% missing)
    # Over 77% missing data. Dropping raw high-cardinality Cabin, 
    # but extracting a valuable binary feature 'Has_Cabin' (1 if cabin was recorded, 0 otherwise)
    df['Has_Cabin'] = df['Cabin'].apply(lambda x: 0 if pd.isna(x) else 1)
    df.drop(columns=['Cabin'], inplace=True)
    print("[OK] Cleaned 'Cabin': Dropped sparse 'Cabin' column (>77% missing) and created 'Has_Cabin' flag (0/1).")
    
    # Verify no missing values remaining in working columns (except Age_Original kept for plotting)
    active_cols = [c for c in df.columns if c != 'Age_Original']
    remaining_nulls = df[active_cols].isnull().sum().sum()
    print(f"\n[OK] Total missing values remaining in cleaned feature set: {remaining_nulls}")
    
    # -------------------------------------------------------------
    # Step 3: Categorical Encoding
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("STEP 2: ENCODING CATEGORICAL VARIABLES ('Sex', 'Embarked')")
    print("-" * 70)
    
    # 1. Encode 'Sex'
    # Binary mapping: 'male' -> 0, 'female' -> 1
    sex_mapping = {'male': 0, 'female': 1}
    df['Sex_Code'] = df['Sex'].map(sex_mapping)
    print(f"[OK] Encoded 'Sex': Mapped 'male' -> 0, 'female' -> 1 (stored in 'Sex_Code' and updated 'Sex').")
    
    # 2. Encode 'Embarked'
    # Mapping ports: 'S' -> 0, 'C' -> 1, 'Q' -> 2
    embarked_mapping = {'S': 0, 'C': 1, 'Q': 2}
    df['Embarked_Code'] = df['Embarked'].map(embarked_mapping)
    print(f"[OK] Encoded 'Embarked' (Label): Mapped 'S' -> 0, 'C' -> 1, 'Q' -> 2 (stored in 'Embarked_Code').")
    
    # Also provide One-Hot Encoding for algorithms preferring dummy features
    embarked_dummies = pd.get_dummies(df['Embarked'], prefix='Embarked', dtype=int)
    for col in embarked_dummies.columns:
        df[col] = embarked_dummies[col]
    print(f"[OK] Encoded 'Embarked' (One-Hot): Created dummy features {list(embarked_dummies.columns)}.")
    
    # Also standardize Sex column as encoded integer for strict ML-ready schema
    # Keep original categorical representation in 'Sex_Label' / 'Embarked_Label' for clarity
    df['Sex_Label'] = df['Sex']
    df['Embarked_Label'] = df['Embarked']
    df['Sex'] = df['Sex_Code']
    df['Embarked'] = df['Embarked_Code']
    
    # -------------------------------------------------------------
    # Step 4: Visualizing Age Distribution
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("STEP 3: VISUALIZING AGE DISTRIBUTION (Matplotlib / Seaborn style)")
    print("-" * 70)
    
    # Set modern visual style
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=300)
    fig.patch.set_facecolor('#F8F9FA')
    
    # Plot 1: Overall Age Distribution with KDE & Statistics
    ax1 = axes[0, 0]
    ax1.set_facecolor('#FFFFFF')
    clean_ages = df['Age']
    counts, bins, patches = ax1.hist(clean_ages, bins=30, density=True, color='#2563EB', alpha=0.6, edgecolor='#1E40AF', linewidth=1)
    
    # Calculate smooth KDE using scipy
    kde_x = np.linspace(0, 85, 500)
    kde = gaussian_kde(clean_ages)
    ax1.plot(kde_x, kde(kde_x), color='#1E3A8A', linewidth=2.5, label='KDE Density')
    
    mean_age = clean_ages.mean()
    median_age = clean_ages.median()
    ax1.axvline(mean_age, color='#DC2626', linestyle='--', linewidth=2, label=f'Mean Age ({mean_age:.1f} yrs)')
    ax1.axvline(median_age, color='#16A34A', linestyle='-', linewidth=2, label=f'Median Age ({median_age:.1f} yrs)')
    
    ax1.set_title('Overall Age Distribution (Cleaned & Imputed)', fontsize=13, fontweight='bold', pad=12, color='#1E293B')
    ax1.set_xlabel('Age (Years)', fontsize=11, fontweight='semibold')
    ax1.set_ylabel('Probability Density', fontsize=11, fontweight='semibold')
    ax1.legend(frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1')
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    # Plot 2: Before vs. After Imputation Comparison
    ax2 = axes[0, 1]
    ax2.set_facecolor('#FFFFFF')
    orig_ages = df['Age_Original'].dropna()
    
    kde_orig = gaussian_kde(orig_ages)
    kde_clean = gaussian_kde(clean_ages)
    
    ax2.hist(orig_ages, bins=30, density=True, alpha=0.35, color='#F59E0B', label='Original (714 records)', edgecolor='#D97706')
    ax2.hist(clean_ages, bins=30, density=True, alpha=0.35, color='#3B82F6', label='Cleaned / Imputed (891 records)', edgecolor='#2563EB')
    ax2.plot(kde_x, kde_orig(kde_x), color='#D97706', linewidth=2.2, label='Original KDE')
    ax2.plot(kde_x, kde_clean(kde_x), color='#1D4ED8', linewidth=2.2, linestyle='--', label='Imputed KDE')
    
    ax2.set_title('Age Distribution: Before vs. After Imputation', fontsize=13, fontweight='bold', pad=12, color='#1E293B')
    ax2.set_xlabel('Age (Years)', fontsize=11, fontweight='semibold')
    ax2.set_ylabel('Density', fontsize=11, fontweight='semibold')
    ax2.legend(frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1')
    ax2.grid(True, linestyle=':', alpha=0.6)
    
    # Plot 3: Age Distribution by Survival Status
    ax3 = axes[1, 0]
    ax3.set_facecolor('#FFFFFF')
    survived_ages = df[df['Survived'] == 1]['Age']
    not_survived_ages = df[df['Survived'] == 0]['Age']
    
    ax3.hist(not_survived_ages, bins=30, density=True, alpha=0.5, color='#EF4444', label='Did Not Survive (0)', edgecolor='#B91C1C')
    ax3.hist(survived_ages, bins=30, density=True, alpha=0.5, color='#10B981', label='Survived (1)', edgecolor='#047857')
    
    kde_surv = gaussian_kde(survived_ages)
    kde_not_surv = gaussian_kde(not_survived_ages)
    ax3.plot(kde_x, kde_not_surv(kde_x), color='#B91C1C', linewidth=2.2)
    ax3.plot(kde_x, kde_surv(kde_x), color='#047857', linewidth=2.2)
    
    ax3.set_title('Age Distribution by Survival Status', fontsize=13, fontweight='bold', pad=12, color='#1E293B')
    ax3.set_xlabel('Age (Years)', fontsize=11, fontweight='semibold')
    ax3.set_ylabel('Density', fontsize=11, fontweight='semibold')
    ax3.legend(frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1')
    ax3.grid(True, linestyle=':', alpha=0.6)
    
    # Plot 4: Age Distribution across Passenger Classes (Boxplot)
    ax4 = axes[1, 1]
    ax4.set_facecolor('#FFFFFF')
    class_1_ages = df[df['Pclass'] == 1]['Age']
    class_2_ages = df[df['Pclass'] == 2]['Age']
    class_3_ages = df[df['Pclass'] == 3]['Age']
    
    box_data = [class_1_ages, class_2_ages, class_3_ages]
    bplot = ax4.boxplot(box_data, patch_artist=True, tick_labels=['1st Class', '2nd Class', '3rd Class'],
                        medianprops=dict(color='#DC2626', linewidth=2),
                        boxprops=dict(linewidth=1.5),
                        whiskerprops=dict(linewidth=1.2),
                        capprops=dict(linewidth=1.2))
    
    colors = ['#93C5FD', '#A7F3D0', '#FDE68A']
    for patch, color in zip(bplot['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_edgecolor('#334155')
        
    ax4.set_title('Age Distribution Across Passenger Classes (Pclass)', fontsize=13, fontweight='bold', pad=12, color='#1E293B')
    ax4.set_xlabel('Passenger Class', fontsize=11, fontweight='semibold')
    ax4.set_ylabel('Age (Years)', fontsize=11, fontweight='semibold')
    ax4.grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    viz_path = 'age_distribution.png'
    plt.savefig(viz_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Visualization saved successfully as '{viz_path}'.")
    
    # -------------------------------------------------------------
    # Step 5: Export the Cleaned Dataset
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("STEP 4: OUTPUT CLEANED DATASET TO NEW CSV")
    print("-" * 70)
    
    # Drop temporary plotting column
    export_df = df.drop(columns=['Age_Original'])
    
    # Save cleaned dataframe to CSV
    export_df.to_csv(output_csv, index=False)
    print(f"[OK] Cleaned dataset saved to '{output_csv}'")
    print(f"    - Cleaned Rows: {export_df.shape[0]}")
    print(f"    - Cleaned Columns ({export_df.shape[1]}): {list(export_df.columns)}")
    
    print("\nFirst 5 rows of cleaned dataset:")
    print(export_df[['PassengerId', 'Survived', 'Pclass', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', 'Embarked', 'Has_Cabin']].head())
    
    print("\nSummary Statistics of Cleaned Dataset:")
    print(export_df[['Age', 'Sex', 'Embarked', 'Fare', 'Has_Cabin']].describe())
    
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    return export_df

if __name__ == '__main__':
    run_data_cleaning_pipeline()
