import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

def execute_policy_audit():
    # 1. Load your empirical data matrix
    try:
        df = pd.read_csv("governance_matrix.csv")
    except FileNotFoundError:
        print("Error: Please create 'governance_matrix.csv' first.")
        return

    # 2. Compute the literal numeric Sovereignty Ratio (Hf / Hs)
    # This captures the capital-to-human mismatch metric
    df['S_r'] = df['H_f'] / df['H_s']
    
    # 3. Create a binary treatment indicator for the policy cutoff
    # time_period > 0 represents the post-CHIPS Act capital regime
    df['post_policy'] = (df['time_period'] >= 0).astype(int)
    
    # 4. Fit the Causal Regression Model
    # We evaluate how time, the policy pivot, and the Sr ratio affect attrition
    model = smf.ols(formula="attrition_rate ~ time_period + post_policy + S_r", data=df).fit()
    
    # 5. Output the verification summary for journal review
    print("\n" + "="*70)
    print("      REGRESSION DISCONTINUITY ANALYSIS: CHIPS POLICY IMPACT      ")
    print("="*70)
    print(model.summary())
    
    # Save the computed columns back to the matrix for repository health
    df.to_csv("governance_matrix.csv", index=False)
    print("\n[SUCCESS] Matrix updated with computed S_r and post_policy indicators.")

if __name__ == "__main__":
    execute_policy_audit()
