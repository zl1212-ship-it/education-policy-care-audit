import json
import numpy as np
import pandas as pd
import requests
import statsmodels.formula.api as smf

def fetch_live_chips_data():
    """Fetches real-time CHIPS Act microelectronics funding allocations from USAspending."""
    url = "https://usaspending.gov"
    
    payload = {
        "filters": {
            "award_ids": [],
            "award_type_codes": ["02", "03", "04", "05"],  # Grants & Cooperative Agreements
            "agencies": [{"type": "funding", "tier": "toptier", "name": "Department of Commerce"}],
            "keywords": ["semiconductor", "microelectronics", "cleanroom", "CHIPS Act"],
            "time_period": [{"start_date": "2022-10-01", "end_date": "2026-01-01"}]
        },
        "fields": [
            "Award ID", "Recipient Name", "Start Date", 
            "Award Amount", "Awarding Agency", "Description"
        ],
        "limit": 100,
        "page": 1
    }
    
    headers = {"Content-Type": "application/json"}
    print("Connecting to official USAspending API Gateway...")
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    if response.status_code == 200:
        awards = response.json().get("results", [])
        df_api = pd.DataFrame(awards)
        print(f"[API SUCCESS] Pulled {len(df_api)} live federal infrastructure awards.")
        return df_api
    else:
        print(f"[API ERROR] Connection failed with status code: {response.status_code}")
        return None

def execute_policy_audit():
    """Processes the panel data and fits the Two-Way Fixed Effects regression model."""
    # 1. Load your localized longitudinal matrix layer
    try:
        df = pd.read_csv("governance_matrix.csv")
    except FileNotFoundError:
        print("Error: Please locate or generate 'governance_matrix.csv' first.")
        return

    print("Processing metrics and calculating normalized ratios...")
    # 2. Compute the Logarithmically Scaled Sovereignty Ratio (S_r)
    # Replicates the per-capita normalization and log transformation: ln( H_f / (H_s * N_g) )
    df['S_r'] = np.log(df['H_f'] / (df['H_s'] * df['N_g']))

    # 3. Create the post-policy implementation binary cutoff flag
    df['post_policy'] = (df['time_period'] >= 0).astype(int)

    # 4. Fit the Causal Regression Model using Two-Way Fixed Effects (TWFE)
    # C(institution) handles entity fixed effects; C(quarter) handles temporal trends
    print("Fitting Two-Way Fixed Effects (TWFE) Panel Model...")
    formula = "attrition_rate ~ post_policy + S_r + C(institution) + C(quarter)"
    model = smf.ols(formula=formula, data=df).fit(cov_type='HC1')

    # 5. Output the verification summary for journal submission verification
    print("\n" + "="*75)
    print("     REPLICATION MODEL: TWO-WAY FIXED EFFECTS (TWFE) PANEL REGRESSION     ")
    print("="*75)
    print(model.summary())

    # Save the computed columns back to the matrix for repository synchronization
    df.to_csv("governance_matrix.csv", index=False)
    print("\n[SUCCESS] Matrix layers updated and synchronized with paper parameters.")

if __name__ == "__main__":
    # Optional: Fetch live benchmarks to look at raw trends
    df_live = fetch_live_chips_data()
    
    # Execute the primary econometric evaluation
    execute_policy_audit()
