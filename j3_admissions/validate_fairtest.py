"""
External validation of the IPEDS-derived test-optional treatment against FairTest's
independently curated roster of ACT/SAT-optional colleges.

FairTest builds its list by hand-verifying institutional policies; it is the standard external
reference. We download FairTest's public hard-copy list (a post-pandemic superset), and check
what share of the 237 pre-COVID IPEDS-coded adopters appear on it. High concordance bounds the
false-positive rate of the reqt_test_scores-based coding.

Writes data/revision_fairtest.csv (matched flag per adopter) and prints the concordance rate.
"""
import os, re, csv, urllib.request, json, time
import pypdf

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
PDF_URL = "https://fairtest.org/sites/default/files/OptionalPDFHardCopy.pdf"
PDF = "/tmp/fairtest.pdf"


def norm(s):
    s = s.lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(the|of|at|university|college|institute|state|main|campus|and)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def get(url):
    for a in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.load(r)
        except Exception:
            if a == 4:
                return {"results": []}
            time.sleep(2)


def main():
    if not os.path.exists(PDF):
        urllib.request.urlretrieve(PDF_URL, PDF)
    blob = norm("\n".join(p.extract_text() or "" for p in pypdf.PdfReader(PDF).pages))
    tokenset = set(blob.split())

    treat = {int(r["unitid"]): r["cohort"] for r in csv.DictReader(open(os.path.join(DATA, "treatment_panel.csv")))}
    pre = [u for u, c in treat.items() if c == "pre_covid"]
    dirr = get("https://educationdata.urban.org/api/v1/college-university/ipeds/"
               "directory/2018/?per_page=10000")["results"]
    name = {x["unitid"]: x.get("inst_name") for x in dirr}

    rows = []
    for u in pre:
        nm = name.get(u) or ""
        toks = [t for t in norm(nm).split() if len(t) > 2]
        core = " ".join(toks)
        hit = bool(core) and (core in blob or all(t in tokenset for t in toks))
        rows.append({"unitid": u, "name": nm, "on_fairtest": int(hit)})

    with open(os.path.join(DATA, "revision_fairtest.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["unitid", "name", "on_fairtest"]); w.writeheader(); w.writerows(rows)

    n = len(rows); m = sum(r["on_fairtest"] for r in rows)
    print(f"pre-COVID adopters: {n}; on FairTest roster: {m} ({100*m/n:.1f}%)")
    print("not matched:")
    for r in rows:
        if not r["on_fairtest"]:
            print("  ", r["unitid"], r["name"])


if __name__ == "__main__":
    main()
