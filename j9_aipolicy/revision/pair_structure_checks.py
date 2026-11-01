"""Who resembles whom at the endpoint: the system-pair structure behind Table S4e, checked for the
small British pool and for text length.

Rebuilds the variant S7 documents and the series TF-IDF fit exactly as seed_convergence.py does
and checks that the endpoint pair matrix replicates Table S4e. Then, on the last-quarter documents:
  1. each institution's mean similarity to the institutions of every system, with its word count
     and the page types that carry its AI text;
  2. the 15 British same-country pairs one by one, and the British row with each British
     institution left out in turn;
  3. British-to-US minus British-to-(AU, CA) similarity, with a permutation p (system labels
     shuffled among the non-British institutions);
  4. the pair matrix with every institution's text cut to its first 300 and 600 words (vectorizer
     refit on the cut documents, as in the endpoint tests of seed_convergence.py);
  5. pair-group means (US pairs, Commonwealth same-country, Commonwealth cross-country,
     US-Commonwealth) and the contrast Commonwealth cross-country minus US-Commonwealth, with a
     permutation p (labels shuffled over all institutions), on full text, at 300 and 600 words,
     and on the pre-shock page text of all sample institutions cut to 600 words (the placebo text
     of seed_convergence.py);
  6. the per-system same-minus-cross gap (as in Table S4d) for the same four texts.
The pooled gaps on the cut and pre-shock texts are checked against seed_convergence_endpoint.csv
and seed_placebo_text.csv. Permutations: 2,000 draws, p = (b + 1) / (B + 1), two-sided."""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
OUT = AN
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
sys.path.insert(0, str(REV))
import seed_convergence as SC
C = SC.C
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
SYS = SC.SYS


def refit(texts):
    X = TfidfVectorizer(ngram_range=(1, 2), min_df=2, stop_words="english", max_features=4000).fit_transform(texts)
    return cosine_similarity(X)


def pair_groups(S, lab):
    n = len(lab); iu = np.triu_indices(n, 1); a = lab[iu[0]]; b = lab[iu[1]]; v = S[iu]
    g = {"US-US": (a == "US") & (b == "US"), "Cw same country": (a != "US") & (b != "US") & (a == b),
         "Cw cross country": (a != "US") & (b != "US") & (a != b), "US-Cw": (a == "US") ^ (b == "US")}
    return {k: (float(v[m].mean()) if m.any() else np.nan, int(m.sum())) for k, m in g.items()}


def block_stat(S):
    def f(lab):
        g = pair_groups(S, lab)
        return g["Cw cross country"][0] - g["US-Cw"][0]
    return f


def main():
    C.page_allowed = lambda u, p, r: True
    sample = set(pd.read_csv(AN / "seed_samples.csv", dtype=str).unitid)
    snaps = pd.DataFrame(SC.load_xn_snaps() + SC.load_seed_snaps() + SC.load_backfill_snaps())
    snaps = snaps[snaps.uid.isin(sample)].reset_index(drop=True)
    names = snaps.groupby("uid")["inst"].first()
    print("institutions with pages:", snaps.uid.nunique(), "| snapshots:", len(snaps), flush=True)

    docs = SC.build_docs(snaps, "S7")
    X = TfidfVectorizer(ngram_range=(1, 2), min_df=3, stop_words="english", max_features=5000).fit_transform(docs["doc"])
    ser, mats = C.quarterly_series(X, docs); k_end = int(ser.event_q.max())
    S, lab, uid = mats[k_end]; n = len(lab)
    print(f"endpoint quarter {k_end}: n = {n}", {s: int((lab == s).sum()) for s in SYS}, flush=True)

    ref = pd.read_csv(AN / "seed_system_pair_matrix.csv"); ref = ref[(ref.rung == "S7") & (ref.pages == "all")]
    chk = C.system_matrix(S, lab).merge(ref, on=["sys_a", "sys_b"], suffixes=("", "_ref"))
    assert ((chk.mean_cos.round(4) == chk.mean_cos_ref.round(4)) & (chk.n_pairs == chk.n_pairs_ref)).all(), "Table S4e does not replicate"
    print("Table S4e replicates (16/16 cells)", flush=True)

    # 1. per-institution means
    has = {}
    for pt in ("integrity", "ai"):
        dp = SC.build_docs(snaps, "S7", ptypes=[pt]); has[pt] = set(dp[dp.event_q == k_end].uid)
    end_doc = docs[docs.event_q == k_end].set_index("uid")["doc"]
    rows = []
    for i in range(n):
        r = {"unitid": uid[i], "institution": names.get(uid[i], ""), "system": lab[i], "words": len(end_doc[uid[i]].split()),
             "pages_with_ai_text": "+".join(p for p in ("integrity", "ai") if uid[i] in has[p])}
        for s in SYS:
            js = [j for j in range(n) if j != i and lab[j] == s]
            r[f"to_{s}"] = round(float(np.mean(S[i, js])), 4) if js else np.nan
        rows.append(r)
    per = pd.DataFrame(rows).sort_values(["system", "words"], ascending=[True, False])
    per.to_csv(OUT / "pair_per_institution.csv", index=False)

    # 2. British pairs and leave-one-out
    uk = [i for i in range(n) if lab[i] == "UK"]
    pd.DataFrame([{"a": names[uid[i]], "b": names[uid[j]], "cos": round(float(S[i, j]), 4)} for x, i in enumerate(uk) for j in uk[x + 1:]]
                 ).sort_values("cos", ascending=False).to_csv(OUT / "british_pairs.csv", index=False)
    def brow(keep):
        m = {}
        for s in SYS:
            v = [S[i, j] for x, i in enumerate(keep) for j in keep[x + 1:]] if s == "UK" else [S[i, j] for i in keep for j in range(n) if lab[j] == s]
            m[f"UK_{s}"] = round(float(np.mean(v)), 4); m[f"pairs_{s}"] = len(v)
        return m
    loo = [{"left_out": "none", "words_left_out": np.nan, **brow(uk)}]
    for i in uk:
        loo.append({"left_out": names[uid[i]], "words_left_out": len(end_doc[uid[i]].split()), **brow([u for u in uk if u != i])})
    pd.DataFrame(loo).to_csv(OUT / "british_row_leave_one_out.csv", index=False)

    # 3. British-to-US minus British-to-(AU, CA)
    non = np.array([j for j in range(n) if lab[j] != "UK"])
    def bstat(l):
        return float(S[np.ix_(uk, non[l == "US"])].mean() - S[np.ix_(uk, non[l != "US"])].mean())
    obs = bstat(lab[non]); rng = np.random.default_rng(13)
    perm = np.array([bstat(rng.permutation(lab[non])) for _ in range(2000)])
    p = float((np.sum(np.abs(perm) >= abs(obs)) + 1) / (len(perm) + 1))
    ukper = per[per.system == "UK"]
    pd.DataFrame([{"contrast": "UK-US minus UK-(AU,CA)", "value": round(obs, 4), "p": round(p, 4), "n_uk": len(uk),
                   "uk_closer_to_US": int((ukper.to_US > ukper[["to_AU", "to_CA"]].mean(axis=1)).sum())}]).to_csv(OUT / "british_us_contrast.csv", index=False)

    # 4-6. texts by length
    dq = docs[docs.event_q == k_end].reset_index(drop=True); lab_q = dq["sys"].to_numpy()
    texts = {"full": (S, lab)}
    for nw in (300, 600):
        texts[f"cut {nw}"] = (refit(dq["doc"].apply(lambda t: " ".join(t.split()[:nw]))), lab_q)
    pre, plab = [], []
    for u, g in snaps.groupby("uid"):
        parts = []
        for url, gp in g.groupby("url"):
            gpre = gp[gp["ts"] < C.SHOCK]
            if len(gpre):
                parts.append(C.texts_of(gpre.sort_values("ts").iloc[-1]["path"], g["sys"].iloc[0])["full_L4"])
        t = " ".join(x for x in parts if x).strip()
        if t:
            pre.append(" ".join(t.split()[:600])); plab.append(g["sys"].iloc[0])
    texts["pre-shock page text, cut 600"] = (refit(pre), np.asarray(plab))

    endref = pd.read_csv(AN / "seed_convergence_endpoint.csv"); endref = endref[(endref.rung == "S7") & endref.gap.notna()].iloc[0]
    plref = pd.read_csv(AN / "seed_placebo_text.csv"); plref = plref[(plref.rung == "S7") & (plref.text == "preshock_text_cap600")].iloc[0]
    mats_rows, grp_rows, sys_rows = [], [], []
    for name, (Sx, lx) in texts.items():
        g0, _ = SC.perm_p(SC.gap_stat(Sx), lx)
        want = {"full": endref.gap, "cut 300": endref.gap_t300, "cut 600": endref.gap_t600, "pre-shock page text, cut 600": plref.gap}[name]
        assert round(g0, 4) == round(want, 4), f"pooled gap does not replicate for {name}: {g0} vs {want}"
        if name != "full":
            m = C.system_matrix(Sx, lx); m.insert(0, "text", name); mats_rows.append(m)
        gg = pair_groups(Sx, lx); b, pb = SC.perm_p(block_stat(Sx), lx, seed=17)
        grp_rows.append({"text": name, "n_inst": len(lx), "pooled_gap": round(g0, 4),
                         **{f"{k} mean": round(v[0], 4) for k, v in gg.items()}, **{f"{k} pairs": v[1] for k, v in gg.items()},
                         "Cw cross minus US-Cw": round(b, 4), "p": round(pb, 4)})
        for r in SC.per_system(Sx, lx):
            sys_rows.append({"text": name, **r})
    print("pooled gaps replicate seed_convergence_endpoint.csv and seed_placebo_text.csv", flush=True)
    pd.concat(mats_rows).to_csv(OUT / "pair_matrix_by_length.csv", index=False)
    pd.DataFrame(grp_rows).to_csv(OUT / "pair_groups_by_length.csv", index=False)
    pd.DataFrame(sys_rows).to_csv(OUT / "per_system_gap_by_length.csv", index=False)

    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    for f in ("pair_per_institution", "british_pairs", "british_row_leave_one_out", "british_us_contrast", "pair_matrix_by_length",
              "pair_groups_by_length", "per_system_gap_by_length"):
        print(f"\n== {f} ==\n", pd.read_csv(OUT / f"{f}.csv").to_string(index=False))


if __name__ == "__main__":
    main()
