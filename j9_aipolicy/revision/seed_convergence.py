"""Convergence analysis on the symmetric page design, restricted to the 89 sample institutions.
Text variants: S1 clean; S4 fully normalized; S7 normalized + strict AI vocabulary (primary);
S7x = S7 with the AI-naming vocabulary itself removed (ai, generative, genai, chatgpt, gpt, llm).
For each variant: quarterly series (pooled and by pair group, with pair counts), a balanced-pool
series (institutions carrying AI text from quarter 5 onward), endpoint tests computed on the
LAST-QUARTER documents of the same series fit (so levels match Figure 1): pooled same-country
gap, Commonwealth-only gap, US-vs-rest contrast, each on full text and on text cut to 300 and 600
words; per-system same-minus-cross decomposition with permutation p; pair matrices overall and by
page type (integrity pages only; AI pages only); top terms; placebos on the sample (AI text,
non-AI text, pre-shock text, paired excess), overall and by group."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import sys, warnings, csv, re
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
sys.path.insert(0, str(REV))
import convergence_ladder as C
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
SYS = ["US", "UK", "AU", "CA"]
AI_NAMES = re.compile(r"(?<![a-z])(?:artificial intelligence|generative|genai|gen ai|chatgpt|chat gpt|gpt|llms?|large language models?|ai|a\.i\.|openai|copilot|bard|gemini|claude)(?![a-z])", re.I)
TEXTKEY = {"S1": "L1", "S4": "L4", "S7": "L7", "S7x": "L7"}


def load_seed_snaps():
    rows = [r for r in csv.DictReader(open(AN / "seed_snapshot_index.csv")) if r.get("bytes") not in ("", "0", None)]
    out, seen = [], set()
    for r in rows:
        p = AN / r["local_path"]
        if p.exists() and r["local_path"] not in seen:
            seen.add(r["local_path"])
            out.append({"uid": str(r["unitid"]), "inst": r["institution"], "sys": "US", "url": r["original_url"], "ptype": r["page_type"],
                        "ts": pd.to_datetime(r["timestamp"], format="%Y%m%d%H%M%S"), "path": p})
    return out


def load_backfill_snaps():
    f = AN / "seed_backfill_pages.csv"
    if not f.exists():
        return []
    keep = set(map(tuple, pd.read_csv(f, dtype=str).values))
    rows = [r for r in csv.DictReader(open(C.PIPE / "data" / "snapshot_index.csv")) if r.get("bytes") not in ("", "0", None)]
    out = []
    for r in rows:
        key = (str(r["unitid"]), Path(r["local_path"]).stem.rsplit("__", 1)[0]); p = C.PIPE / r["local_path"]
        if key in keep and p.exists():
            out.append({"uid": str(r["unitid"]), "inst": r["institution"], "sys": "US", "url": r["original_url"], "ptype": r["page_type"],
                        "ts": pd.to_datetime(r["timestamp"], format="%Y%m%d%H%M%S"), "path": p})
    return out


def load_xn_snaps():
    rows = [r for r in csv.DictReader(open(C.XN / "data" / "snapshot_index.csv")) if r.get("bytes") not in ("", "0", None)]
    out = []
    for r in rows:
        p = C.XN / r["local_path"]
        if p.exists():
            out.append({"uid": str(r["unitid"]), "inst": r["institution"], "sys": r["state"], "url": r["original_url"], "ptype": r["page_type"],
                        "ts": pd.to_datetime(r["timestamp"], format="%Y%m%d%H%M%S"), "path": p})
    return out


def text_for(path, sysname, variant):
    t = C.texts_of(path, sysname)[TEXTKEY[variant]]
    if variant == "S7x":
        t = " ".join(AI_NAMES.sub(" ", t).split())
    return t


def build_docs(snaps, variant, ptypes=None):
    docs = []
    for uid, g in snaps.groupby("uid"):
        sysname = g["sys"].iloc[0]
        if ptypes is not None:
            g = g[g["ptype"].isin(ptypes)]
        for k, qe in C.QEND.items():
            parts = []
            for url, gp in g.groupby("url"):
                sub = gp[gp["ts"] <= qe]
                if len(sub):
                    parts.append(text_for(sub.sort_values("ts").iloc[-1]["path"], sysname, variant))
            doc = " ".join(p for p in parts if p).strip()
            if doc:
                docs.append({"uid": uid, "sys": sysname, "event_q": k, "doc": doc})
    return pd.DataFrame(docs).reset_index(drop=True)


def perm_p(stat_fn, labels, nperm=2000, seed=3):
    rng = np.random.default_rng(seed); obs = stat_fn(np.asarray(labels))
    perm = np.array([stat_fn(rng.permutation(labels)) for _ in range(nperm)])
    perm = perm[~np.isnan(perm)]
    return obs, float((np.sum(np.abs(perm) >= abs(obs)) + 1) / (len(perm) + 1))


def gap_stat(S):
    n = S.shape[0]; iu = np.triu_indices(n, 1); v = S[iu]
    def f(lab):
        same = (lab[:, None] == lab[None, :])[iu]
        return float(v[same].mean() - v[~same].mean()) if same.any() and (~same).any() else np.nan
    return f


def usrest_stat(S):
    n = S.shape[0]; iu = np.triu_indices(n, 1); v = S[iu]
    def f(lab):
        us = (lab == "US"); both = (us[:, None] & us[None, :])[iu]; mixed = (us[:, None] ^ us[None, :])[iu]
        return float(v[both].mean() - v[mixed].mean()) if both.any() and mixed.any() else np.nan
    return f


def endpoint_tests(docs_q, S_q, prefix=""):
    """Tests on the last-quarter documents: full text uses the series matrix S_q; truncated
    versions refit a vectorizer on the cut documents."""
    out = {}
    sysv = docs_q["sys"].to_numpy()
    def run(S, tag):
        g, p = perm_p(gap_stat(S), sysv); out[f"{prefix}gap{tag}"], out[f"{prefix}p{tag}"] = round(g, 4), round(p, 4)
        non = sysv != "US"
        if non.sum() >= 8 and len(set(sysv[non])) >= 2:
            g2, p2 = perm_p(gap_stat(S[np.ix_(non, non)]), sysv[non]); out[f"{prefix}cw_gap{tag}"], out[f"{prefix}cw_p{tag}"] = round(g2, 4), round(p2, 4)
        g3, p3 = perm_p(usrest_stat(S), sysv, seed=5); out[f"{prefix}usrest{tag}"], out[f"{prefix}usrest_p{tag}"] = round(g3, 4), round(p3, 4)
        n = S.shape[0]; iu = np.triu_indices(n, 1); same = (sysv[:, None] == sysv[None, :])[iu]
        out[f"{prefix}within{tag}"], out[f"{prefix}cross{tag}"] = round(float(S[iu][same].mean()), 4), round(float(S[iu][~same].mean()), 4)
    run(S_q, "")
    for n in (300, 600):
        cut = docs_q["doc"].apply(lambda t: " ".join(t.split()[:n]))
        X = TfidfVectorizer(ngram_range=(1, 2), min_df=2, stop_words="english", max_features=4000).fit_transform(cut)
        run(cosine_similarity(X), f"_t{n}")
    out[f"{prefix}n"] = len(docs_q); out[f"{prefix}n_us"] = int((sysv == "US").sum())
    out[f"{prefix}words_median_US"] = float(np.median([len(t.split()) for t, s in zip(docs_q["doc"], sysv) if s == "US"])) if (sysv == "US").any() else np.nan
    out[f"{prefix}words_median_nonUS"] = float(np.median([len(t.split()) for t, s in zip(docs_q["doc"], sysv) if s != "US"])) if (sysv != "US").any() else np.nan
    return out


def per_system(S, sysv):
    rows = []; n = S.shape[0]; iu = np.triu_indices(n, 1); v = S[iu]; a = sysv[iu[0]]; b = sysv[iu[1]]
    for s in SYS:
        same = (a == s) & (b == s); cross = ((a == s) ^ (b == s))
        if same.sum() >= 3 and cross.sum() >= 3:
            def f(lab, s=s):
                aa = lab[iu[0]]; bb = lab[iu[1]]; sm = (aa == s) & (bb == s); cr = ((aa == s) ^ (bb == s))
                return float(v[sm].mean() - v[cr].mean()) if sm.any() and cr.any() else np.nan
            g, p = perm_p(f, sysv, seed=7)
            rows.append({"system": s, "n_inst": int((sysv == s).sum()), "same_pairs": int(same.sum()), "cross_pairs": int(cross.sum()),
                         "same_mean": round(float(v[same].mean()), 4), "cross_mean": round(float(v[cross].mean()), 4), "gap": round(g, 4), "p": round(p, 4)})
    return rows


def groups_series(mats):
    rows = []
    for k, (Sk, sysk, _) in mats.items():
        n = len(sysk); iu = np.triu_indices(n, 1); a = sysk[iu[0]]; b = sysk[iu[1]]; v = Sk[iu]
        groups = {"US-US": (a == "US") & (b == "US"), "Commonwealth same country": (a != "US") & (b != "US") & (a == b),
                  "Commonwealth cross country": (a != "US") & (b != "US") & (a != b), "US-Commonwealth": (a == "US") ^ (b == "US")}
        for g, m in groups.items():
            rows.append({"event_q": k, "group": g, "n_pairs": int(m.sum()), "mean_cos": round(float(v[m].mean()), 4) if m.any() else np.nan})
    return rows


def main():
    C.page_allowed = lambda u, p, r: True
    sample = set(pd.read_csv(AN / "seed_samples.csv", dtype=str).unitid)
    snaps = pd.DataFrame(load_xn_snaps() + load_seed_snaps() + load_backfill_snaps())
    snaps = snaps[snaps.uid.isin(sample)].reset_index(drop=True)
    print("sample institutions with pages:", snaps.uid.nunique(), "of", len(sample), "| snapshots:", len(snaps), flush=True)
    for i, (p, s) in enumerate(zip(snaps["path"], snaps["sys"]), 1):
        C.texts_of(p, s)
        if i % 400 == 0: print(f"  text {i}/{len(snaps)}", flush=True)
    series_rows, group_rows, balanced_rows, end_rows, mat_rows, persys_rows, term_rows, plac_rows, comp_rows = [], [], [], [], [], [], [], [], []
    for variant in TEXTKEY:
        docs = build_docs(snaps, variant)
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, stop_words="english", max_features=5000); X = vec.fit_transform(docs["doc"])
        ser, mats = C.quarterly_series(X, docs); ser.insert(0, "rung", variant); series_rows.append(ser)
        for r in groups_series(mats): group_rows.append({"rung": variant, **r})
        # balanced pool: institutions with AI text in every quarter from 5 to the end
        k_end = int(ser.event_q.max()); present = docs.groupby("uid").event_q.apply(set)
        keep = {u for u, ks in present.items() if all(k in ks for k in range(5, k_end + 1))}
        db = docs[docs.uid.isin(keep) & (docs.event_q >= 5)].reset_index(drop=True)
        if db.uid.nunique() >= 8:
            Xb = vec.transform(db["doc"]); serb, matsb = C.quarterly_series(Xb, db)
            for r in groups_series(matsb): balanced_rows.append({"rung": variant, "n_inst": db.uid.nunique(), **r})
        # endpoint tests on the last-quarter docs of the series fit
        dq = docs[docs.event_q == k_end].reset_index(drop=True); S_q, sysv, _ = mats[k_end]
        ev = endpoint_tests(dq, S_q); ev.update({"rung": variant, "end_quarter": k_end, "first_quarter": int(ser.event_q.min())}); end_rows.append(ev)
        for r in per_system(S_q, sysv): persys_rows.append({"rung": variant, **r})
        m = C.system_matrix(S_q, sysv); m.insert(0, "rung", variant); m["pages"] = "all"; mat_rows.append(m)
        for lab, pts in (("integrity", ["integrity"]), ("ai", ["ai"])):
            dp = build_docs(snaps, variant, ptypes=pts)
            if len(dp) and dp.event_q.max() >= 10:
                Xp = TfidfVectorizer(ngram_range=(1, 2), min_df=3, stop_words="english", max_features=5000).fit_transform(dp["doc"])
                kp = int(dp.event_q.max()); dqp = dp[dp.event_q == kp].reset_index(drop=True)
                if dqp.uid.nunique() >= 8:
                    Sp = cosine_similarity(Xp[dqp.index.to_numpy()]); mp = C.system_matrix(Sp, dqp["sys"].to_numpy()); mp.insert(0, "rung", variant); mp["pages"] = lab; mat_rows.append(mp)
                    evp = endpoint_tests(dqp, Sp, prefix=f"{lab}_"); evp.update({"rung": variant, "end_quarter": kp}); end_rows.append(evp)
                    for r in per_system(Sp, dqp["sys"].to_numpy()): persys_rows.append({"rung": variant + ":" + lab, **r})
        term_rows.append(C.top_terms(vec, X, docs, k_end, variant, ntop=30))
        comp = dq.groupby("sys").size().reindex(SYS).fillna(0).astype(int)
        for sname in SYS: comp_rows.append({"rung": variant, "system": sname, "n_inst_end": int(comp[sname])})
        print(f"[{variant}] q{k_end} n={len(dq)} (US {int((sysv=='US').sum())}): within {ev['within']:.3f} cross {ev['cross']:.3f} gap {ev['gap']:+.4f} p={ev['p']:.3f} | "
              f"t300 gap {ev['gap_t300']:+.4f} p={ev['p_t300']:.3f} | Commonwealth gap {ev.get('cw_gap', float('nan')):+.4f} p={ev.get('cw_p', float('nan')):.3f}, t300 {ev.get('cw_gap_t300', float('nan')):+.4f} p={ev.get('cw_p_t300', float('nan')):.3f} | "
              f"US-vs-rest {ev['usrest']:+.4f} p={ev['usrest_p']:.3f}, t300 {ev['usrest_t300']:+.4f} p={ev['usrest_p_t300']:.3f}", flush=True)
        # placebos on the sample: AI text (cap 600), non-AI text (cap 600), pre-shock text (cap 600), paired excess; overall and by group
        if variant in ("S1", "S7"):
            tk = TEXTKEY[variant]; nonkey = "nonai_L1" if tk == "L1" else "nonai_L4"; prekey = "full_L1" if tk == "L1" else "full_L4"
            ai_rows, non_rows, pre_rows, sysv2, sysv_pre = [], [], [], [], []
            for uid, g in snaps.groupby("uid"):
                sysname = g["sys"].iloc[0]; a_parts, n_parts, p_parts = [], [], []
                for url, gp in g.groupby("url"):
                    t = C.texts_of(gp.sort_values("ts").iloc[-1]["path"], sysname); a_parts.append(t[tk]); n_parts.append(t[nonkey])
                    gpre = gp[gp["ts"] < C.SHOCK]
                    if len(gpre): p_parts.append(C.texts_of(gpre.sort_values("ts").iloc[-1]["path"], sysname)[prekey])
                a = " ".join(x for x in a_parts if x).strip(); nn = " ".join(x for x in n_parts if x).strip(); pr = " ".join(x for x in p_parts if x).strip()
                if a and nn: ai_rows.append(" ".join(a.split()[:600])); non_rows.append(" ".join(nn.split()[:600])); sysv2.append(sysname)
                if pr: pre_rows.append(" ".join(pr.split()[:600])); sysv_pre.append(sysname)
            def tests(texts, labels, label):
                X = TfidfVectorizer(ngram_range=(1, 2), min_df=2, stop_words="english", max_features=4000).fit_transform(texts); S = cosine_similarity(X); lab = np.asarray(labels)
                g, p = perm_p(gap_stat(S), lab); row = {"rung": variant, "text": label, "n_inst": len(lab), "gap": round(g, 4), "p": round(p, 4)}
                non = lab != "US"
                if non.sum() >= 8 and len(set(lab[non])) >= 2:
                    g2, p2 = perm_p(gap_stat(S[np.ix_(non, non)]), lab[non]); row["cw_gap"], row["cw_p"] = round(g2, 4), round(p2, 4)
                g3, p3 = perm_p(usrest_stat(S), lab, seed=5); row["usrest"], row["usrest_p"] = round(g3, 4), round(p3, 4)
                return row, S
            r1, Sa = tests(ai_rows, sysv2, "ai_text_cap600"); r2, Sn = tests(non_rows, sysv2, "nonai_text_cap600"); r3, _ = tests(pre_rows, sysv_pre, "preshock_text_cap600")
            D = Sa - Sn; lab = np.asarray(sysv2); g, p = perm_p(gap_stat(D), lab, seed=11); r4 = {"rung": variant, "text": "paired_excess_ai_minus_nonai_cap600", "n_inst": len(lab), "gap": round(g, 4), "p": round(p, 4)}
            non = lab != "US"
            if non.sum() >= 8: g2, p2 = perm_p(gap_stat(D[np.ix_(non, non)]), lab[non], seed=11); r4["cw_gap"], r4["cw_p"] = round(g2, 4), round(p2, 4)
            g3, p3 = perm_p(usrest_stat(D), lab, seed=5); r4["usrest"], r4["usrest_p"] = round(g3, 4), round(p3, 4)
            plac_rows += [r1, r2, r3, r4]
            for r in (r1, r2, r3, r4): print(f"   [{r['text']}] n={r['n_inst']} gap {r['gap']:+.4f} p={r['p']:.3f} | Commonwealth {r.get('cw_gap', float('nan')):+.4f} p={r.get('cw_p', float('nan')):.3f} | US-vs-rest {r['usrest']:+.4f} p={r['usrest_p']:.3f}", flush=True)
    pd.concat(series_rows).to_csv(AN / "seed_convergence_series.csv", index=False); pd.DataFrame(group_rows).to_csv(AN / "seed_convergence_groups.csv", index=False)
    pd.DataFrame(balanced_rows).to_csv(AN / "seed_convergence_balanced.csv", index=False); pd.DataFrame(end_rows).to_csv(AN / "seed_convergence_endpoint.csv", index=False)
    pd.concat(mat_rows).to_csv(AN / "seed_system_pair_matrix.csv", index=False); pd.DataFrame(persys_rows).to_csv(AN / "seed_per_system_gap.csv", index=False)
    pd.concat(term_rows).to_csv(AN / "seed_top_terms.csv", index=False); pd.DataFrame(plac_rows).to_csv(AN / "seed_placebo_text.csv", index=False)
    pd.DataFrame(comp_rows).to_csv(AN / "seed_endpoint_composition.csv", index=False)
    print("done", flush=True)
if __name__ == "__main__":
    main()
