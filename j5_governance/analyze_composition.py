"""Board-composition audit: educator representation on state boards of education.

Two layers, both from public sources with provenance:
  1. RULES  (data/board_composition_rules_2026.csv): whether each state's law MANDATES educator/
     stakeholder seats, BARS current educators/school employees, and whether it seats a VOTING
     teacher. Each row cites the statute or the NASBE/EdWeek compilation.
  2. COMPOSITION (data/board_members_2026.csv): the occupational background of current members,
     hand-collected from official board rosters (source URL + as_of per member). Coverage is
     PARTIAL (occupation identifiable for a minority of seats); every statistic is reported with
     its coverage and is a descriptive supplement to the rules, not a precise census.

All statistics below are emitted by this script; nothing is hand-entered into prose. Ohio and
Montana rosters were not machine-accessible and carry no member rows (coverage n/a).

Output: data/composition_results.csv
"""
import os
import pandas as pd, numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
rules = pd.read_csv(os.path.join(DATA, "board_composition_rules_2026.csv"))
mem   = pd.read_csv(os.path.join(DATA, "board_members_2026.csv"))
panel = pd.read_csv(os.path.join(DATA, "governance_panel.csv"))
panel = panel[panel.board_exists == 1]

mem = mem[mem.is_educator.isin([0, 1])].copy(); mem.is_educator = mem.is_educator.astype(int)
reg = mem[~mem.role.isin(["student", "ex-officio"])]          # regular elected/appointed members

R = {}   # results dict

# ---- Layer 1: rules ----
b = rules[rules.state_abbr.isin(panel.state_abbr)]            # 47 board states
R["n_boards"] = len(b)
R["mandate_educator_or_stakeholder"] = int(b.educator_mandate.sum())
R["bar_current_educators"]           = int(b.educator_bar.sum())
R["voting_teacher_seat"]             = int((b.teacher_seat == "voting").sum())
R["advisory_teacher_seat"]           = int((b.teacher_seat == "advisory").sum())

# ---- Layer 2: composition (regular members, coded) ----
R["members_coded"]  = len(reg)
R["boards_with_members"] = reg.state_abbr.nunique()
R["educator_share_overall_pct"] = round(reg.is_educator.mean() * 100, 1)
bl = reg.groupby("state_abbr").is_educator.agg(n_coded="count", n_edu="sum").reset_index()
bl["edu_share"] = bl.n_edu / bl.n_coded
bl = bl.merge(rules[["state_abbr", "educator_mandate", "educator_bar"]], on="state_abbr", how="left")
bl = bl.merge(panel[["state_abbr", "board_regime", "n_voting", "rep_index", "auth_index",
                     "algorithmic_grade", "naep_g4_math_equiv"]], on="state_abbr", how="left")
bl["coverage"] = bl.n_coded / bl.n_voting
R["median_board_coverage_pct"] = round(bl.coverage.median() * 100, 1)
R["board_edu_share_mean_pct"]  = round(bl.edu_share.mean() * 100, 1)
R["boards_ge60pct_educator"]   = int((bl.edu_share >= 0.60).sum())
R["boards_le25pct_educator"]   = int((bl.edu_share <= 0.25).sum())

# mandate -> educator composition
a = bl.loc[bl.educator_mandate == 1, "edu_share"]; z = bl.loc[bl.educator_mandate == 0, "edu_share"]
t, p = stats.ttest_ind(a, z, equal_var=False)
R["edu_share_mandate_pct"] = round(a.mean() * 100, 1); R["edu_share_nomandate_pct"] = round(z.mean() * 100, 1)
R["edu_share_mandate_welch_p"] = round(p, 4)

# LOWER BOUND (identifiability check): code every UNidentified seat as a non-educator, so the
# educator share is n_edu / n_voting. If easier-to-identify members drove the mandate gap, the gap
# should vanish under this most-conservative coding. It narrows but the direction holds.
bl["edu_share_lb"] = bl.n_edu / bl.n_voting
alb = bl.loc[bl.educator_mandate == 1, "edu_share_lb"]; zlb = bl.loc[bl.educator_mandate == 0, "edu_share_lb"]
tlb, plb = stats.ttest_ind(alb, zlb, equal_var=False)
R["edu_share_lb_overall_pct"] = round((bl.n_edu.sum() / bl.n_voting.sum()) * 100, 1)
R["edu_share_lb_mandate_pct"] = round(alb.mean() * 100, 1); R["edu_share_lb_nomandate_pct"] = round(zlb.mean() * 100, 1)
R["edu_share_lb_welch_p"] = round(plb, 4)

# relational (descriptive; small n, partial coverage -> report, do not over-read)
for c in ["rep_index", "auth_index", "algorithmic_grade", "naep_g4_math_equiv"]:
    d = bl[["edu_share", c]].dropna()
    rho, pv = stats.spearmanr(d.edu_share, d[c])
    R[f"spearman_eduShare_{c}"] = round(rho, 3); R[f"spearman_eduShare_{c}_p"] = round(pv, 3)

out = pd.DataFrame(sorted(R.items()), columns=["metric", "value"])
out.to_csv(os.path.join(DATA, "composition_results.csv"), index=False)

print("=== RULES (of 47 boards) ===")
print(f"  mandate educator/stakeholder seat : {R['mandate_educator_or_stakeholder']}")
print(f"  bar current educators/employees   : {R['bar_current_educators']}")
print(f"  voting teacher seat               : {R['voting_teacher_seat']}   advisory: {R['advisory_teacher_seat']}")
print("=== COMPOSITION (regular members; PARTIAL coverage) ===")
print(f"  members coded: {R['members_coded']} across {R['boards_with_members']} boards; median board coverage {R['median_board_coverage_pct']}%")
print(f"  educator background overall: {R['educator_share_overall_pct']}%  | board mean {R['board_edu_share_mean_pct']}%")
print(f"  bimodal: {R['boards_ge60pct_educator']} boards >=60% educator, {R['boards_le25pct_educator']} boards <=25%")
print(f"  MANDATE effect: {R['edu_share_mandate_pct']}% (mandate) vs {R['edu_share_nomandate_pct']}% (none), Welch p={R['edu_share_mandate_welch_p']}")
print(f"  LOWER BOUND (unidentified=non-educator): overall {R['edu_share_lb_overall_pct']}%; "
      f"mandate {R['edu_share_lb_mandate_pct']}% vs non-mandate {R['edu_share_lb_nomandate_pct']}%, Welch p={R['edu_share_lb_welch_p']}")
print("=== RELATIONAL (descriptive; small n, partial coverage) ===")
for c in ["rep_index", "auth_index", "algorithmic_grade", "naep_g4_math_equiv"]:
    print(f"  Spearman(edu_share, {c}) = {R['spearman_eduShare_'+c]:+}, p={R['spearman_eduShare_'+c+'_p']}")
print(f"\nwrote {os.path.join(DATA, 'composition_results.csv')}")
