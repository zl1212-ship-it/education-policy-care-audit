"""Fetch the two public scored-essay corpora used by this pipeline.

Sources (both CC BY-NC-SA 4.0, released by the Learning Agency Lab):

1. PERSUADE 2.0 — 25k+ argumentative essays by U.S. 6th-12th graders, human
   holistic scores (1-6) plus writer demographics including ELL status.
   Repo: github.com/scrosseye/persuade_corpus_2.0 (CSVs hosted on Google Drive;
   the test zip's password is published in that repo's README).
   Citation: Crossley, Baffour, Tian, Franklin, Benner & Boser (2024),
   Assessing Writing 61, 100865.

2. ELLIPSE — ~6.5k essays by English-language-learner students, human holistic
   + six analytic proficiency scores, plus a raw per-rater score file for the
   full ~9k-essay scoring effort (rater-level disagreement benchmark).
   Repo: github.com/scrosseye/ELLIPSE-Corpus (files in-repo; zip passwords are
   published in that repo's README).
   Citation: Crossley, Tian, Baffour, Franklin, Kim, Morris, Benner, Picou &
   Boser (2023), International Journal of Learner Corpus Research 9(2), 248-269.

Output: data/raw/ (gitignored; reproducible by rerunning this script).
Stdlib only. Zip passwords below are public documentation, not secrets.
ELLIPSE_REF is pinned to a commit SHA; the PERSUADE Drive files are versioned
by the release README.
"""
from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

RAW = Path(__file__).parent / "data" / "raw"

ELLIPSE_REPO = "scrosseye/ELLIPSE-Corpus"
# pinned 2026-06-12 so the corpus cannot drift under the analysis
ELLIPSE_REF = "dc3b8f0b3b4332fc9f64302c4ccfc4ed582f4b43"
ELLIPSE_FILES = {
    "ELLIPSE_Final_github_train.csv": None,
    "ELLIPSE_Final_github_test.zip": b"ellipse_test",
    "ellipsis_raw_rater_scores_anon_all_essay.zip": b"ellipse_raw_data",
}

# Google Drive file ids from the persuade_corpus_2.0 README
PERSUADE_FILES = {
    "persuade_2.0_human_scores_demo_id_github.csv": (
        "13phHyDzIsb0MHyJr6q-B-qIa9P2tM135", None),
    "persuade_corpus_2.0_test.zip": (
        "1K1SIJiG-2zWgMlTzxQeYOcLwOsFaVel1", b"persuade_test"),
}


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "j8-fetch"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def _save(name: str, blob: bytes, password: bytes | None) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / name
    out.write_bytes(blob)
    print(f"  {name}: {len(blob)/1e6:.1f} MB")
    if name.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            z.extractall(RAW, pwd=password)
            for m in z.namelist():
                print(f"    extracted {m}")


def main() -> int:
    print("ELLIPSE corpus ...")
    for name, pwd in ELLIPSE_FILES.items():
        url = (f"https://raw.githubusercontent.com/{ELLIPSE_REPO}/"
               f"{ELLIPSE_REF}/{name}")
        _save(name, _get(url), pwd)

    print("PERSUADE 2.0 corpus ...")
    for name, (fid, pwd) in PERSUADE_FILES.items():
        url = (f"https://drive.usercontent.google.com/download?id={fid}"
               f"&export=download&confirm=t")
        _save(name, _get(url), pwd)

    print("Done. Raw files under", RAW)
    return 0


if __name__ == "__main__":
    sys.exit(main())
