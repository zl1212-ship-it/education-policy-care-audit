#!/usr/bin/env python3
"""
Policy Analytics Metrics Engine
Calculates the Sovereignty Ratio (Sr) and Survival to Study Ratio (Rss) 
to model temporal constraints and institutional funding alignment.
"""

def calculate_sovereignty_ratio(infra_funding: float, student_subsistence: float) -> float:
    """Calculates Sr = Hf / Hs"""
    if student_subsistence <= 0:
        raise ValueError("Student subsistence support must be strictly greater than zero.")
    return round(infra_funding / student_subsistence, 4)

def calculate_survival_to_study_ratio(time_survival: float, time_research: float) -> float:
    """Calculates Rss = Tsurvival / Tresearch"""
    if time_research <= 0:
        raise ValueError("Funded research hours must be strictly greater than zero.")
    return round(time_survival / time_research, 4)

def evaluate_institutional_state(sr: float, rss: float) -> dict:
    """Classifies risk states based on empirical threshold values."""
    status = {
        "funding_risk": "Optimal Alignment" if sr <= 1.0 else "Life Stall Accel Acceleration",
        "temporal_status": "Sovereign Preservation" if rss < 0.5 else "Systemic Time Poverty"
    }
    return status

if __name__ == "__main__":
    print("="*60)
    print("      TRANSNATIONAL EDUCATION POLICY AUDIT SYSTEM ENGINE      ")
    print("="*60)
    
    # Representative Macro Case Example Data
    cases = [
        {"regime": "US CHIPS Act Framework (Underfunded Stipend Scenario)", "hf": 500000, "hs": 32000, "ts": 25, "tr": 20},
        {"regime": "Japan Society 5.0 (Platform Displace Scenario)", "hf": 450000, "hs": 42000, "ts": 12, "tr": 35}
    ]
    
    for case in cases:
        print(f"\n[+] Evaluating Strategic Policy Regime: {case['regime']}")
        
        # Execute equations
        sr_val = calculate_sovereignty_ratio(case['hf'], case['hs'])
        rss_val = calculate_survival_to_study_ratio(case['ts'], case['tr'])
        diagnostics = evaluate_institutional_state(sr_val, rss_val)
        
        print(f"    - Sovereignty Ratio (Sr)          : {sr_val}")
        print(f"    - Survival to Study Ratio (Rss)   : {rss_val}")
        print(f"    - Funding Architecture Diagnostic : {diagnostics['funding_risk']}")
        print(f"    - Staffing/Temporal Diagnostic    : {diagnostics['temporal_status']}")
        print("-"*60)
