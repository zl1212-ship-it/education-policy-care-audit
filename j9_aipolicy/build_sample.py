"""Build the institution sampling frame for the AI-policy event study.

Frame
-----
A stratified cross-section of US colleges across Carnegie basic type
(R1 / R2 / M master's / BAC baccalaureate-liberal-arts / AC associate's) and
control (Public / Private nonprofit). The 50 public state flagships are
DELIBERATELY EXCLUDED: they are the unit of `j6_detection/`, whose census codes
the *current* policy text for detector-evidence stance. This pipeline tracks a
disjoint set of institutions and a disjoint construct (how the *durable*
integrity page's text moved *over time* around the ChatGPT shock), so the two
papers share no corpus, unit, or outcome.

Per institution the frame records the durable academic-integrity / honor-code /
conduct page (the page that existed before the shock, where AI language would
later be added; not an AI-guidance microsite created after the shock) and merges
the IPEDS nonresident-alien enrollment share as the continuous differential-
exposure intensity. The Wayback coverage filter that finally decides which
institutions enter the panel lives in fetch_snapshots.py / build_panel.py; this
script only assembles candidates and their covariates.

Source notes and the IPEDS race coding are in SOURCES.md. Stdlib only.
Output: data/sample_frame.csv
"""
import csv
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "data" / "sample_frame.csv"
EXPOSURE_YEAR = 2022  # pre-shock fall enrollment (shock = 2022-11-30)
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"

CONTROL_CODE = {"Public": 1, "Private": 2}

# institution, state, control, carnegie, durable integrity URL, GenAI-guidance URL, pilot
# The institution-quarter outcome takes the max restrictiveness across the two pages
# (build_panel.py), so a thin or wrong guidance URL only contributes zero; the
# integrity page anchors the pre-shock baseline.
INSTITUTIONS = [
    # --- Private R1 ---
    ("Massachusetts Institute of Technology", "MA", "Private", "R1", "https://integrity.mit.edu/", "https://teaching.mit.edu/ai/", True),
    ("Stanford University", "CA", "Private", "R1", "https://communitystandards.stanford.edu/policies-and-guidance/honor-code", "https://teachingcommons.stanford.edu/teaching-guides/artificial-intelligence-teaching-guide", True),
    ("Harvard University", "MA", "Private", "R1", "https://honorcouncil.fas.harvard.edu/honor-code", "https://oue.fas.harvard.edu/ai-guidance", True),
    ("Yale University", "CT", "Private", "R1", "https://catalog.yale.edu/academic-regulations/honesty-plagiarism/", "https://poorvucenter.yale.edu/AIguidance", True),
    ("Princeton University", "NJ", "Private", "R1", "https://odoc.princeton.edu/curriculum/academic-integrity-princeton", "https://mcgraw.princeton.edu/undergraduates/resources/resources-generative-ai", True),
    ("Columbia University", "NY", "Private", "R1", "https://www.college.columbia.edu/academics/academicintegrity", "https://provost.columbia.edu/content/office-senior-vice-provost/generative-ai", False),
    ("University of Pennsylvania", "PA", "Private", "R1", "https://catalog.upenn.edu/pennbook/code-of-academic-integrity/", "https://tll.seas.upenn.edu/generative-ai-resources/", True),
    ("Duke University", "NC", "Private", "R1", "https://studentaffairs.duke.edu/conduct/z-policies/duke-community-standard", "https://learninginnovation.duke.edu/ai-and-teaching-at-duke-2/", False),
    ("Northwestern University", "IL", "Private", "R1", "https://www.northwestern.edu/provost/policies-procedures/academic-integrity/index.html", "https://www.northwestern.edu/aiprinciples/", False),
    ("Johns Hopkins University", "MD", "Private", "R1", "https://studentaffairs.jhu.edu/policies-guidelines/undergrad-ethics/", "https://cldt.jhu.edu/ai-and-teaching/", False),
    ("University of Southern California", "CA", "Private", "R1", "https://sjacs.usc.edu/students/academic-integrity/", "https://cet.usc.edu/generative-ai-resources/", True),
    ("New York University", "NY", "Private", "R1", "https://www.nyu.edu/about/policies-guidelines-compliance/policies-and-guidelines/academic-integrity-for-students-at-nyu.html", "https://www.nyu.edu/faculty/teaching-and-learning-resources/instructional-technology/generative-ai.html", False),
    ("Carnegie Mellon University", "PA", "Private", "R1", "https://www.cmu.edu/policies/student-and-student-life/academic-integrity.html", "https://www.cmu.edu/teaching/technology/aitools/index.html", True),
    ("Vanderbilt University", "TN", "Private", "R1", "https://www.vanderbilt.edu/student_handbook/the-honor-system/", "https://www.vanderbilt.edu/generative-ai/", False),
    ("Emory University", "GA", "Private", "R1", "http://catalog.college.emory.edu/academic/policy/honor-code.html", "https://ai.emory.edu/", False),
    ("University of Notre Dame", "IN", "Private", "R1", "https://honorcode.nd.edu/", "https://provost.nd.edu/about/committees-and-initiatives/teaching-and-learning-with-generative-ai/", False),
    ("Boston University", "MA", "Private", "R1", "https://www.bu.edu/academics/policies/academic-conduct-code/", "https://www.bu.edu/ctl/guides/using-generative-ai-in-courses/", True),
    ("Northeastern University", "MA", "Private", "R1", "https://catalog.northeastern.edu/undergraduate/academic-policies-procedures/academic-integrity-policy/", "https://provost.northeastern.edu/aiguidance/", False),
    ("Tufts University", "MA", "Private", "R1", "https://students.tufts.edu/student-affairs/student-life-policies/academic-integrity-policy", "https://provost.tufts.edu/generative-ai-guidance", False),
    ("Rice University", "TX", "Private", "R1", "https://honor.rice.edu/honor-system-handbook", "https://ai.rice.edu/", False),
    ("Brown University", "RI", "Private", "R1", "https://college.brown.edu/design-your-education/academic-policies/academic-code", "https://www.brown.edu/sheridan/teaching-learning-resources/teaching-resources/classroom-practices/learning-context/generative-ai", False),
    ("Cornell University", "NY", "Private", "R1", "https://theuniversityfaculty.cornell.edu/academic-integrity/", "https://teaching.cornell.edu/generative-artificial-intelligence", False),
    ("University of Chicago", "IL", "Private", "R1", "https://college.uchicago.edu/advising/academic-integrity-student-conduct", "https://academictech.uchicago.edu/2023/01/24/chatgpt-and-ai-in-the-classroom/", False),
    ("Washington University in St Louis", "MO", "Private", "R1", "https://wustl.edu/about/compliance-policies/academic-policies/undergraduate-student-academic-integrity-policy/", "https://ctl.wustl.edu/resources/generative-ai-and-teaching/", False),

    # --- Public R1 (non-flagship) ---
    ("University of California-Los Angeles", "CA", "Public", "R1", "https://deanofstudents.ucla.edu/academic-integrity", "https://teaching.ucla.edu/resources/ai_pedagogy/", True),
    ("University of California-San Diego", "CA", "Public", "R1", "https://academicintegrity.ucsd.edu/", "https://academicintegrity.ucsd.edu/faculty/AI-guidelines.html", True),
    ("University of California-Davis", "CA", "Public", "R1", "https://ossja.ucdavis.edu/academic-integrity", "https://teachingcommons.ucdavis.edu/generative-ai", False),
    ("University of California-Irvine", "CA", "Public", "R1", "https://aisc.uci.edu/students/academic-integrity/index.php", "https://dtei.uci.edu/generative-ai/", False),
    ("Texas A & M University", "TX", "Public", "R1", "https://aggiehonor.tamu.edu/", "https://ai.tamu.edu/", True),
    ("Michigan State University", "MI", "Public", "R1", "https://ombud.msu.edu/academic-integrity", "https://genai.msu.edu/", False),
    ("Purdue University", "IN", "Public", "R1", "https://www.purdue.edu/odos/osrr/academic-integrity/index.html", "https://www.purdue.edu/innovativelearning/teaching-with-ai/", True),
    ("Arizona State University", "AZ", "Public", "R1", "https://provost.asu.edu/academic-integrity", "https://provost.asu.edu/generative-ai", False),
    ("Georgia Institute of Technology", "GA", "Public", "R1", "https://policylibrary.gatech.edu/student-affairs/academic-honor-code", "https://ctl.gatech.edu/ai-teaching-learning", False),
    ("Virginia Polytechnic Institute and State University", "VA", "Public", "R1", "https://www.honorsystem.vt.edu/", "https://tlos.vt.edu/initiatives/generative-ai.html", False),
    ("North Carolina State University", "NC", "Public", "R1", "https://studentconduct.dasa.ncsu.edu/academic-integrity/", "https://teaching-resources.delta.ncsu.edu/generative_ai/", False),
    ("Florida State University", "FL", "Public", "R1", "https://fda.fsu.edu/academic-resources/academic-integrity-and-grievances/academic-honor-policy", "https://distance.fsu.edu/instructors/generative-ai-resources", False),
    ("University of Cincinnati", "OH", "Public", "R1", "https://www.uc.edu/about/policies/academic-integrity.html", "https://www.uc.edu/about/provost/academic-affairs/digital-futures/generative-ai.html", False),
    ("Temple University", "PA", "Public", "R1", "https://bulletin.temple.edu/undergraduate/academic-policies/academic-rights-responsibilities/", "https://teaching.temple.edu/generative-ai", False),
    ("University of Pittsburgh", "PA", "Public", "R1", "https://www.provost.pitt.edu/info/academic-integrity-guidelines", "https://teaching.pitt.edu/resources/teaching-with-generative-ai/", False),
    ("Stony Brook University", "NY", "Public", "R1", "https://www.stonybrook.edu/commcms/academic_integrity/", "https://www.stonybrook.edu/cft/teaching-resources/generative-ai/", False),
    ("University of Houston", "TX", "Public", "R1", "https://www.uh.edu/provost/policies/honesty/", "https://www.uh.edu/cte/resources/generative-ai/", False),
    ("Colorado State University", "CO", "Public", "R1", "https://www.studentresolutioncenter.colostate.edu/avoiding-academic-misconduct/", "https://tilt.colostate.edu/generative-ai/", False),
    ("Oregon State University", "OR", "Public", "R1", "https://studentlife.oregonstate.edu/studentconduct/academic-misconduct-0", "https://ctl.oregonstate.edu/generative-ai-teaching", False),

    # --- Public R2 / Master's ---
    ("San Diego State University", "CA", "Public", "R2", "https://sacd.sdsu.edu/cssr/student-affairs/academic-integrity", "https://its.sdsu.edu/ai/", False),
    ("James Madison University", "VA", "Public", "M", "https://www.jmu.edu/honorcode/", "https://www.jmu.edu/cfi/teaching-resources/ai.shtml", True),
    ("California Polytechnic State University-San Luis Obispo", "CA", "Public", "M", "https://academicprograms.calpoly.edu/content/academicpolicies/academic-integrity", "https://ctlt.calpoly.edu/genai", False),
    ("San Jose State University", "CA", "Public", "R2", "https://www.sjsu.edu/studentconduct/policies/academic-integrity.php", "https://www.sjsu.edu/cfd/resources/generative-ai.php", False),
    ("Towson University", "MD", "Public", "M", "https://www.towson.edu/provost/academicaffairs/academic-integrity.html", "https://www.towson.edu/academics/resources/generative-ai/", False),
    ("Montclair State University", "NJ", "Public", "R2", "https://www.montclair.edu/policies/all-policies/academic-integrity-policy/", "https://www.montclair.edu/faculty-excellence/teaching-resources/generative-ai/", False),

    # --- Private baccalaureate / liberal arts ---
    ("Williams College", "MA", "Private", "BAC", "https://www.williams.edu/honor-system/", "https://oit.williams.edu/help/generative-ai/", True),
    ("Amherst College", "MA", "Private", "BAC", "https://www.amherst.edu/campuslife/community-standards/honor-code", "https://www.amherst.edu/offices/centers/center-for-teaching-and-learning/teaching-resources/generative-ai", False),
    ("Swarthmore College", "PA", "Private", "BAC", "https://www.swarthmore.edu/student-handbook/academic-misconduct", "https://www.swarthmore.edu/its/generative-ai", False),
    ("Wellesley College", "MA", "Private", "BAC", "https://www.wellesley.edu/honorcode", "https://www.wellesley.edu/lts/generative-ai", False),
    ("Middlebury College", "VT", "Private", "BAC", "https://www.middlebury.edu/college/policies/honor-code", "https://sites.middlebury.edu/ai/", False),
    ("Bowdoin College", "ME", "Private", "BAC", "https://www.bowdoin.edu/dean-of-students/judicial-board/academic-honor-principle/index.html", "https://www.bowdoin.edu/baldwin-center/teaching-guides/generative-ai.html", False),
    ("Carleton College", "MN", "Private", "BAC", "https://www.carleton.edu/handbook/academics/", "https://www.carleton.edu/learning-teaching-center/resources/generative-ai/", False),
    ("Davidson College", "NC", "Private", "BAC", "https://www.davidson.edu/about/distinctly-davidson/honor-code", "https://www.davidson.edu/offices-and-services/teaching-learning/generative-ai", False),
    ("Smith College", "MA", "Private", "BAC", "https://www.smith.edu/about-smith/smith-history/honor-code", "https://www.smith.edu/academics/faculty/teaching-learning/generative-ai", False),
    ("Oberlin College", "OH", "Private", "BAC", "https://www.oberlin.edu/dean-of-students/honor-system", "https://www.oberlin.edu/center-teaching-innovation-excellence/generative-ai", False),
    ("Macalester College", "MN", "Private", "BAC", "https://www.macalester.edu/academics/academicprograms/academicpolicies/academicintegrity/", "https://www.macalester.edu/serie/generative-ai/", True),
    ("Grinnell College", "IA", "Private", "BAC", "https://www.grinnell.edu/about/leadership/offices-services/academic-advising/resources/academic-honesty", "https://www.grinnell.edu/about/offices-services/center-teaching-learning/generative-ai", False),
    ("Haverford College", "PA", "Private", "BAC", "https://www.haverford.edu/honor-council/code", "https://www.haverford.edu/provost/generative-ai", False),

    # --- Public associate's / community ---
    ("Santa Monica College", "CA", "Public", "AC", "https://www.smc.edu/student-support/academic-support/scholars/honor-code.php", "https://www.smc.edu/academics/center-teaching-excellence/generative-ai.php", False),
    ("Northern Virginia Community College", "VA", "Public", "AC", "https://www.nvcc.edu/about/policies/academic.html", "https://www.nvcc.edu/academics/generative-ai.html", False),
    ("De Anza College", "CA", "Public", "AC", "https://www.deanza.edu/studenthandbook/academic-integrity.html", "https://www.deanza.edu/online-ed/generative-ai.html", False),
    ("Houston Community College", "TX", "Public", "AC", "https://www.hccs.edu/about-hcc/policies/", "https://www.hccs.edu/resources-for/faculty-and-staff/generative-ai/", False),
]

STATE_FIPS = {
    "AL": 1, "AK": 2, "AZ": 4, "AR": 5, "CA": 6, "CO": 8, "CT": 9, "DE": 10,
    "FL": 12, "GA": 13, "HI": 15, "ID": 16, "IL": 17, "IN": 18, "IA": 19,
    "KS": 20, "KY": 21, "LA": 22, "ME": 23, "MD": 24, "MA": 25, "MI": 26,
    "MN": 27, "MS": 28, "MO": 29, "MT": 30, "NE": 31, "NV": 32, "NH": 33,
    "NJ": 34, "NM": 35, "NY": 36, "NC": 37, "ND": 38, "OH": 39, "OK": 40,
    "OR": 41, "PA": 42, "RI": 44, "SC": 45, "SD": 46, "TN": 47, "TX": 48,
    "UT": 49, "VT": 50, "VA": 51, "WA": 53, "WV": 54, "WI": 55, "WY": 56,
}

# UnitIDs that name-matching cannot resolve unambiguously; verified from IPEDS.
UNITID_OVERRIDE = {
    "Washington University in St Louis": 179867,
    "Stony Brook University": 196097,
    "University of California-Los Angeles": 110662,
    "Texas A & M University": 228723,
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def norm(s):
    s = s.lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(the|at|main campus)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def resolve_unitid(inst, fips, control_code, cache):
    if inst in UNITID_OVERRIDE:
        return UNITID_OVERRIDE[inst]
    key = (fips, control_code)
    if key not in cache:
        d = get(f"{BASE}/directory/{EXPOSURE_YEAR}/?fips={fips}")
        cache[key] = [r for r in d["results"] if r.get("inst_control") == control_code]
    target = norm(inst)
    cands = cache[key]
    for r in cands:
        if norm(r["inst_name"]) == target:
            return r["unitid"]
    for r in cands:
        if norm(r["inst_name"]).startswith(target):
            return r["unitid"]
    tset = set(target.split())
    best = [r for r in cands if tset <= set(norm(r["inst_name"]).split())]
    return best[0]["unitid"] if len(best) == 1 else None


def intl_share(unitid):
    d = get(f"{BASE}/fall-enrollment/{EXPOSURE_YEAR}/99/race/?unitid={unitid}")
    agg = [x for x in d["results"]
           if x["ftpt"] == 99 and x["degree_seeking"] == 99
           and x["class_level"] == 99 and x["sex"] == 99]
    by_race = {x["race"]: x["enrollment_fall"] for x in agg}
    total, nra = by_race.get(99), by_race.get(8)  # race=8 nonresident alien; 9 is race-unknown
    if not total or nra is None:
        return None, None, None
    return total, nra, round(nra / total, 4)


def main():
    cache, rows, missing = {}, [], []
    for inst, st, control, carnegie, url, guidance_url, pilot in INSTITUTIONS:
        fips = STATE_FIPS.get(st)
        ctrl_code = CONTROL_CODE[control]
        uid, total, nra, share = None, None, None, None
        try:
            uid = resolve_unitid(inst, fips, ctrl_code, cache) if fips else None
            if uid:
                total, nra, share = intl_share(uid)
        except Exception as e:
            print(f"  ! IPEDS error for {inst}: {type(e).__name__}: {e}")
        if not uid:
            missing.append(inst)
        rows.append({
            "institution": inst, "state": st, "control": control,
            "carnegie": carnegie, "integrity_url": url, "guidance_url": guidance_url,
            "pilot": int(pilot), "unitid": uid, "exposure_year": EXPOSURE_YEAR,
            "total_enroll": total, "nonresident_alien": nra, "intl_share": share,
        })
        tag = f"intl={share:.1%}" if share is not None else "(intl n/a)"
        print(f"  {inst:<46} {control:<7} {carnegie:<3} uid={str(uid):<7} {tag}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    cols = ["institution", "state", "control", "carnegie", "integrity_url",
            "guidance_url", "pilot", "unitid", "exposure_year", "total_enroll",
            "nonresident_alien", "intl_share"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    n_pilot = sum(r["pilot"] for r in rows)
    n_share = sum(r["intl_share"] is not None for r in rows)
    print(f"\nWrote {OUT}  ({len(rows)} institutions; {n_pilot} pilot; "
          f"{n_share} with intl_share)")
    if missing:
        print(f"UNRESOLVED unitids ({len(missing)}) -> add to UNITID_OVERRIDE: {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
