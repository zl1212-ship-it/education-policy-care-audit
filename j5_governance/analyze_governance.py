"""
J5 analysis: accountability without representation in state education governance.

Reads data/governance_panel.csv and produces every number cited in the paper:
  1. Regime distribution and ENROLLMENT-WEIGHTED student exposure (who cannot elect their board).
  2. The representation deficit (direct election, voting student, voting teacher) by regime.
  3. Authority near-universality and the accountability-representation gap.
  4. "Whose interests": representation vs the demography of the governed
     (means by regime; enrollment-weighted exposure of students of color; OLS with HC3 SE).
  5. Robustness: alternative index weightings, exclusions, rank correlations, bootstrap CIs.

Writes data/results_summary.csv and prints a full console report. No randomness except the
bootstrap (seeded).
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
rng = np.random.default_rng(7)

df = pd.read_csv(os.path.join(DATA, "governance_panel.csv"))
b = df[df.board_exists == 1].copy()           # 47 boards
TOT = df.enrollment_2021.sum()
rows = []                                       # (metric, value) for results_summary.csv

def rec(k, v):
    rows.append({"metric": k, "value": v})
    return v

line = "=" * 78
print(line); print("1. REGIME DISTRIBUTION AND STUDENT EXPOSURE"); print(line)
cnt = df.board_regime.value_counts()
wsh = df.groupby("board_regime").enrollment_2021.sum() / TOT * 100
tab = pd.DataFrame({"n_states": cnt, "enroll_share_pct": wsh.round(1)})
print(tab.to_string())
# headline: students who CANNOT directly elect a majority of their board
not_elected = df[~df.board_regime.eq("elected")].enrollment_2021.sum() / TOT * 100
print(f"\nStudents in states WITHOUT a directly elected board: {not_elected:.1f}%")
rec("pct_students_no_elected_board", round(not_elected, 1))
rec("n_elected_boards", int((b.board_regime == "elected").sum()))
rec("enroll_share_elected", round(wsh.get("elected", 0), 1))
rec("enroll_share_governor", round(wsh.get("governor", 0), 1))
rec("n_no_board", int((df.board_regime == "none").sum()))

print("\n" + line); print("2. THE REPRESENTATION DEFICIT (47 boards)"); print(line)
n = len(b)
for label, col in [("directly elected by public", "is_elected"),
                   ("voting student member", "student_voting"),
                   ("voting teacher member", "teacher_voting"),
                   ("any student member (voting or not)", "student_present")]:
    if col == "is_elected":
        s = (b.board_regime == "elected").astype(int)
    else:
        s = b[col]
    print(f"  {label:<38}: {int(s.sum()):>2}/{n}  ({s.mean()*100:4.1f}%)")
    rec(f"pct_boards_{col}", round(s.mean() * 100, 1))
print(f"\n  mean voting members per board : {b.n_voting.mean():.1f}  "
      f"(range {int(b.n_voting.min())}-{int(b.n_voting.max())})")
print(f"  mean term (years)             : {b.term_years.mean():.1f}")

print("\n" + line); print("3. AUTHORITY AND THE GAP"); print(line)
print(f"  boards that adopt academic standards : {int(b.auth_standards_board.sum())}/{n} "
      f"({b.auth_standards_board.mean()*100:.1f}%)")
print(f"  boards DIRECTLY controlling licensure : {int((b.auth_licensure=='SBE').sum())}/{n} "
      f"({(b.auth_licensure=='SBE').mean()*100:.1f}%)   "
      f"[+{int((b.auth_licensure=='PSC').sum())} via professional standards commission]")
print(f"  constitutionally entrenched boards    : {int(b.constitutional.sum())}/{n} "
      f"({b.constitutional.mean()*100:.1f}%)")
rec("pct_boards_set_standards", round(b.auth_standards_board.mean() * 100, 1))
rec("pct_boards_constitutional", round(b.constitutional.mean() * 100, 1))
# Rep and Auth as distinct dimensions (rank-based, scale-free) + joint-distribution quadrant
rho_ra, p_ra = stats.spearmanr(b.rep_index, b.auth_index)
hi_lo = int(((b.auth_index > 0.5) & (b.rep_index < 0.5)).sum())
corner = int(((b.auth_index >= 0.67) & (b.rep_index <= 0.20)).sum())
print(f"\n  Spearman rho(Rep, Auth)   : {rho_ra:+.3f} (p={p_ra:.3f})  [distinct dimensions]")
print(f"  high-authority/low-representation quadrant: {hi_lo}/{len(b)} "
      f"({hi_lo/len(b)*100:.0f}%);  extreme corner (Auth>=.67 & Rep<=.20): {corner}")
rec("spearman_rep_auth", round(rho_ra, 3)); rec("quadrant_hi_auth_lo_rep", hi_lo); rec("corner_count", corner)
print(f"\n  mean Representation Index : {b.rep_index.mean():.3f}")
print(f"  mean Authority Index      : {b.auth_index.mean():.3f}")
print(f"  mean gap (auth - rep, descriptive heuristic): {b.gap.mean():.3f}")
rec("mean_rep_index", round(b.rep_index.mean(), 3))
rec("mean_auth_index", round(b.auth_index.mean(), 3))
rec("mean_gap", round(b.gap.mean(), 3))
print("\n  Representation & gap by regime:")
g = b.groupby("board_regime").agg(rep=("rep_index", "mean"),
                                  auth=("auth_index", "mean"),
                                  gap=("gap", "mean"), nstates=("state", "size"))
print(g.round(3).to_string())
print("\n  Highest accountability-representation gap (top 8):")
print(b.sort_values("gap", ascending=False)[["state", "board_regime", "auth_index",
      "rep_index", "gap"]].head(8).to_string(index=False))

print("\n" + line); print("4. WHOSE INTERESTS ARE REPRESENTED"); print(line)
b["elected"] = (b.board_regime == "elected").astype(int)
print("  Mean demography by whether the board is directly elected:")
dd = b.groupby("elected").agg(states=("state", "size"),
                              pct_soc=("pct_students_of_color", "mean"),
                              pct_frl=("pct_frl_2122", "mean"),
                              rep=("rep_index", "mean"))
print(dd.round(1).to_string())
# t-test: do appointed-board states have MORE students of color?
soc_el = b.loc[b.elected == 1, "pct_students_of_color"]
soc_ap = b.loc[b.elected == 0, "pct_students_of_color"]
t, p = stats.ttest_ind(soc_ap, soc_el, equal_var=False)
print(f"\n  % students of color, appointed vs elected boards: "
      f"{soc_ap.mean():.1f} vs {soc_el.mean():.1f}  (Welch t={t:.2f}, p={p:.3f})")
rec("soc_appointed_boards", round(soc_ap.mean(), 1))
rec("soc_elected_boards", round(soc_el.mean(), 1))
rec("soc_diff_p", round(p, 3))

# enrollment-weighted exposure: share of SOC vs White students under elected boards
soc_students = (df.enrollment_2021 * df.pct_students_of_color / 100)
white_students = (df.enrollment_2021 * df.pct_white_2021 / 100)
el = df.board_regime == "elected"
soc_el_share = soc_students[el].sum() / soc_students.sum() * 100
white_el_share = white_students[el].sum() / white_students.sum() * 100
print(f"  Of all students of color, {soc_el_share:.1f}% are governed by a directly elected board;")
print(f"  of all White students,    {white_el_share:.1f}% are.")
rec("soc_under_elected_pct", round(soc_el_share, 1))
rec("white_under_elected_pct", round(white_el_share, 1))

# OLS: representation index on demography (HC3 robust SE); FRL dropped (pandemic-noisy) in primary
reg = b.dropna(subset=["rep_index", "pct_students_of_color", "enrollment_2021"]).copy()
reg["log_enroll"] = np.log(reg.enrollment_2021)
X = sm.add_constant(reg[["pct_students_of_color", "log_enroll"]])
m = sm.OLS(reg.rep_index, X).fit(cov_type="HC3")
print("\n  OLS  rep_index ~ pct_students_of_color + log_enroll  (HC3, n=%d):" % len(reg))
print(f"    pct_students_of_color coef = {m.params['pct_students_of_color']:+.5f} "
      f"(p={m.pvalues['pct_students_of_color']:.3f})")
print(f"    log_enroll coef            = {m.params['log_enroll']:+.4f} "
      f"(p={m.pvalues['log_enroll']:.3f})   R^2={m.rsquared:.3f}")
rec("ols_soc_coef", round(m.params["pct_students_of_color"], 5))
rec("ols_soc_p", round(m.pvalues["pct_students_of_color"], 3))

print("\n" + line); print("5. ROBUSTNESS"); print(line)
print(f"  mean gap, equal-weight index            : "
      f"{(b.auth_index - b.rep_index_equal).mean():.3f}")
print(f"  mean gap, WA partial-election credit     : "
      f"{(b.auth_index - b.rep_index_altWA).mean():.3f}")
print(f"  mean gap, excluding DC                   : "
      f"{b[b.state_abbr!='DC'].gap.mean():.3f}")
# Spearman: representation vs students of color (rank-robust)
rho, pr = stats.spearmanr(b.rep_index, b.pct_students_of_color)
print(f"  Spearman rho(rep_index, pct_SOC)         : {rho:+.3f} (p={pr:.3f})")
rec("spearman_rep_soc", round(rho, 3))
# bootstrap CI for the appointed-vs-elected SOC gap
diffs = []
for _ in range(5000):
    ia = rng.choice(soc_ap.values, len(soc_ap), replace=True)
    ie = rng.choice(soc_el.values, len(soc_el), replace=True)
    diffs.append(ia.mean() - ie.mean())
lo, hi = np.percentile(diffs, [2.5, 97.5])
print(f"  bootstrap 95% CI, SOC gap (appointed-elected): [{lo:.1f}, {hi:.1f}] pts")
rec("soc_gap_ci_lo", round(lo, 1)); rec("soc_gap_ci_hi", round(hi, 1))

print("\n" + line); print("6. THE ALGORITHMIC ACCOUNTABILITY LAYER (ECS 2024)"); print(line)
print("  rating-type distribution (51 jurisdictions):")
print(df.rating_category.value_counts().to_string())
algo = b.algorithmic_grade
print(f"\n  boards running a formula-driven summative grade (A-F/star/index): "
      f"{int(algo.sum())}/{len(b)}  ({algo.mean()*100:.1f}%)")
print(f"  boards with any single summative rating               : "
      f"{int(b.summative_any.sum())}/{len(b)}  ({b.summative_any.mean()*100:.1f}%)")
# enrollment-weighted exposure
ew = (df.loc[df.algorithmic_grade == 1, "enrollment_2021"].sum() / TOT * 100)
print(f"  students under a board with an algorithmic grade      : {ew:.1f}%")
rec("pct_boards_algorithmic_grade", round(algo.mean() * 100, 1))
rec("pct_students_algorithmic_grade", round(ew, 1))
# does representation predict algorithmic grading? (honest test of the alternative)
r_alg = b.loc[b.algorithmic_grade == 1, "rep_index"]
r_no = b.loc[b.algorithmic_grade == 0, "rep_index"]
ta, pa = stats.ttest_ind(r_alg, r_no, equal_var=False)
print(f"\n  mean Representation Index: algorithmic-grade boards {r_alg.mean():.3f} "
      f"vs others {r_no.mean():.3f}  (Welch t={ta:.2f}, p={pa:.3f})")
rho2, pr2 = stats.spearmanr(b.rep_index, b.algorithmic_grade)
print(f"  Spearman rho(rep_index, algorithmic_grade): {rho2:+.3f} (p={pr2:.3f})")
rec("rep_algo_diff_p", round(pa, 4)); rec("spearman_rep_algo", round(rho2, 3))

pd.DataFrame(rows).to_csv(os.path.join(DATA, "results_summary.csv"), index=False)
print(f"\nwrote {os.path.join(DATA, 'results_summary.csv')}")
