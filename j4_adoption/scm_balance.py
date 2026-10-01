"""
Covariate description table for the two headline synthetic controls (gsu_grad, csu_ret).
The synthetic control in scm_all.py matches ONLY the pre-treatment outcome path; no
covariates enter the fit. This table therefore DESCRIBES the counterfactual on predictors
measured circa 2010 (2011 fallback where 2010 is missing) rather than validating the fit:
treated value, synthetic value (donor weights from scm_<case>_weights.csv, renormalized
over the donors observed on each predictor), and the unweighted donor-pool mean.

Predictors (Urban Institute Education Data API, cached to data/raw_scm_covariates.csv):
  ug_enroll       total undergraduate fall enrollment (fall-enrollment .../race, race=99)
  urm_share       Black+Hispanic+AmInd+NHPI+two-or-more share of UG fall enrollment
                  (races 2,3,5,6,7 over race=99; same pull pattern as cs_did.py)
  pell_share      share of ALL undergraduates awarded Pell (sfa-all-undergraduates,
                  type_of_aid=5, percent_of_students). Numerator and denominator cover
                  the same all-undergraduate population, avoiding the Pell-recipient /
                  FTFT-retention-cohort mismatch documented for pell_share.csv in
                  robustness.py (type_of_aid=5 verified as Pell against known shares:
                  U Michigan 0.16, UC Berkeley 0.34 in 2010).
  adm_rate        number_admitted / number_applied (admissions-enrollment, sex=99);
                  missing for open-admission institutions
  tuition_instate published in-state UG tuition+fees (academic-year-tuition,
                  level_of_study=1, tuition_type=3, tuition_fees_ft)
  locale_city     urban-centric locale in {11,12,13} (city), 0/1, directory/2010

Treated values: GSU = its own value. CSU = enrollment-weighted mean over the treated
campuses in csu_staging.csv (weights = 2010 UG fall enrollment), the same aggregation
direction as the campus-mean outcome series; locale_city enters as a 0/1 indicator
averaged with the same enrollment weights.
Donor pools are reconstructed exactly as in scm_all.py (complete outcome series required).
Writes data/scm_balance.csv.
"""
import os, json, urllib.request, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
GSU = 139940
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"
YEARS = list(range(2004, 2021))
URM_RACES = {2, 3, 5, 6, 7}


def pull(url):
    out = []
    while url:
        for a in range(6):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    d = json.load(r); break
            except Exception:
                if a == 5: raise
        out += d["results"]; url = d.get("next")
    return out


def ok(v):
    return v is not None and not (isinstance(v, (int, float)) and v < 0)


# ---------- covariate cache ----------
cov_path = os.path.join(DATA, "raw_scm_covariates.csv")
if not os.path.exists(cov_path):
    print("pulling covariates (2010, 2011 fallback) ...", flush=True)
    frames = {}
    for y in (2010, 2011):
        enr = pull(f"{BASE}/fall-enrollment/{y}/1/race/?sex=99&ftpt=99&degree_seeking=99&class_level=99")
        tot = {x["unitid"]: x["enrollment_fall"] for x in enr
               if x["race"] == 99 and ok(x.get("enrollment_fall"))}
        urm = {}
        for x in enr:
            if x["race"] in URM_RACES and ok(x.get("enrollment_fall")):
                urm[x["unitid"]] = urm.get(x["unitid"], 0) + x["enrollment_fall"]
        pell = {x["unitid"]: x["percent_of_students"]
                for x in pull(f"{BASE}/sfa-all-undergraduates/{y}/?type_of_aid=5")
                if ok(x.get("percent_of_students"))}
        adm = {x["unitid"]: x["number_admitted"] / x["number_applied"]
               for x in pull(f"{BASE}/admissions-enrollment/{y}/?sex=99")
               if ok(x.get("number_applied")) and ok(x.get("number_admitted"))
               and x["number_applied"] > 0}
        tui = {x["unitid"]: x["tuition_fees_ft"]
               for x in pull(f"{BASE}/academic-year-tuition/{y}/?level_of_study=1&tuition_type=3")
               if ok(x.get("tuition_fees_ft"))}
        loc = {x["unitid"]: x["urban_centric_locale"]
               for x in pull(f"{BASE}/directory/{y}/")
               if ok(x.get("urban_centric_locale"))}
        frames[y] = dict(tot=tot, urm=urm, pell=pell, adm=adm, tui=tui, loc=loc)
        print(f"  {y} pulled", flush=True)
    uids = set()
    for y in frames:
        for k in frames[y]: uids |= set(frames[y][k])

    def val(uid, key, transform=lambda v: v):
        for y in (2010, 2011):
            if uid in frames[y][key]: return transform(frames[y][key][uid])
        return np.nan
    rows = []
    for u in sorted(uids):
        tot10 = val(u, "tot")
        urm_share = (val(u, "urm") / tot10) if tot10 and tot10 > 0 else np.nan
        rows.append((u, tot10, urm_share, val(u, "pell"), val(u, "adm"), val(u, "tui"),
                     val(u, "loc", lambda v: 1.0 if v in (11, 12, 13) else 0.0)))
    pd.DataFrame(rows, columns=["unitid", "ug_enroll", "urm_share", "pell_share",
                                "adm_rate", "tuition_instate", "locale_city"]) \
        .to_csv(cov_path, index=False)
cov = pd.read_csv(cov_path).set_index("unitid")
PREDICTORS = ["ug_enroll", "urm_share", "pell_share", "adm_rate", "tuition_instate", "locale_city"]

# ---------- donor pools, reconstructed as in scm_all.py ----------
dir_path = os.path.join(DATA, "raw_directory.csv")
if not os.path.exists(dir_path):
    rows = pull(f"{BASE}/directory/2021/?inst_control=1")
    pd.DataFrame([(x["unitid"], x.get("inst_name"), x.get("state_abbr"),
                   x.get("institution_level"), x.get("inst_size")) for x in rows],
                 columns=["unitid", "inst_name", "state_abbr", "institution_level",
                          "inst_size"]).to_csv(dir_path, index=False)
dirr = pd.read_csv(dir_path)
pub4 = dirr[dirr.institution_level == 4]
size5 = dict(zip(pub4[pub4.inst_size == 5].unitid, pub4[pub4.inst_size == 5].state_abbr))
large = dict(zip(pub4[pub4.inst_size.isin([4, 5])].unitid,
                 pub4[pub4.inst_size.isin([4, 5])].state_abbr))
exclude = {GSU}
for f in ["treatment_panel.csv", "csu_staging.csv"]:
    exclude |= set(pd.read_csv(os.path.join(DATA, f))["unitid"].tolist())
csu_ids = sorted(set(pd.read_csv(os.path.join(DATA, "csu_staging.csv"))["unitid"].tolist()))


def load(name):
    df = pd.read_csv(os.path.join(DATA, f"raw_{name}.csv"))
    return {(int(r.uid), int(r.year)): r.val for r in df.itertuples()}


def complete(src, u):
    return all((u, y) in src for y in YEARS)


grad_t, ret = load("grad_t"), load("ret")
gsu_donors = sorted(u for u, st in size5.items()
                    if u not in exclude and st != "GA" and complete(grad_t, u))
csu_donors = sorted(u for u, st in large.items()
                    if u not in exclude and st != "CA" and complete(ret, u))
print(f"pools: gsu_grad {len(gsu_donors)} donors, csu_ret {len(csu_donors)} donors")


def wmean(vals, wts):
    v = np.asarray(vals, float); w = np.asarray(wts, float)
    m = ~np.isnan(v)
    return float((v[m] * w[m]).sum() / w[m].sum()) if w[m].sum() > 0 else np.nan, int(m.sum())


rows = []
for case, donors in [("gsu_grad", gsu_donors), ("csu_ret", csu_donors)]:
    wdf = pd.read_csv(os.path.join(DATA, f"scm_{case}_weights.csv"))
    wmap = dict(zip(wdf.unitid, wdf.weight))
    if case == "gsu_grad":
        treated = {p: (cov.loc[GSU, p] if GSU in cov.index else np.nan) for p in PREDICTORS}
        n_treated = 1
    else:  # CSU aggregate: enrollment-weighted over treated campuses
        cc = cov.reindex(csu_ids)
        ew = cc["ug_enroll"].fillna(0).values
        treated = {p: wmean(cc[p].values, ew)[0] for p in PREDICTORS}
        n_treated = int((~cc["ug_enroll"].isna()).sum())
    dc = cov.reindex(donors)
    dw = np.array([wmap.get(u, 0.0) for u in donors])
    for p in PREDICTORS:
        syn, n_syn = wmean(dc[p].values, dw)
        pool = float(np.nanmean(dc[p].values)); n_pool = int((~dc[p].isna()).sum())
        rows.append({"case": case, "predictor": p, "treated": treated[p],
                     "synthetic": syn, "pool_mean": pool,
                     "n_pool_observed": n_pool, "n_treated_units": n_treated,
                     "year": "2010 (2011 fallback)"})
        print(f"{case:8s} {p:16s} treated={treated[p]:12.3f}  synth={syn:12.3f}  "
              f"pool={pool:12.3f}  (obs {n_pool}/{len(donors)})")

pd.DataFrame(rows).to_csv(os.path.join(DATA, "scm_balance.csv"), index=False)
print("\nsaved data/scm_balance.csv")
