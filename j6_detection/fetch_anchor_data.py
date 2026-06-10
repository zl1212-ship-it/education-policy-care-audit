"""Fetch the public human-essay corpora used as J6's anchor.

Source: Liang et al. (2023), "GPT detectors are biased against non-native English
writers" (Patterns 4:100779), released at github.com/Weixin-Liang/ChatGPT-Detector-Bias.

We pull only the HUMAN-written essays. Because every essay here is human-authored, any
detector that labels one "AI-generated" is producing a false accusation; the audit in
analyze_detection.py measures how that false-positive rate splits by the author's
native vs non-native English status.

Output: data/anchor/ (the repo's Data_and_Results tree, verbatim). Stdlib only.
Pin REF to a commit SHA before the manuscript freeze so the corpus cannot drift.
"""
import io
import json
import sys
import tarfile
import urllib.request
from pathlib import Path

REPO = "Weixin-Liang/ChatGPT-Detector-Bias"
REF = "main"  # TODO: pin to a commit SHA at manuscript freeze
DEST = Path(__file__).parent / "data" / "anchor"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "j6-fetch"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def default_branch() -> str:
    try:
        meta = json.loads(_get(f"https://api.github.com/repos/{REPO}"))
        return meta.get("default_branch", REF)
    except Exception as e:  # offline / rate-limited: fall back to REF
        print(f"  (could not query default branch: {e}; using '{REF}')")
        return REF


def main() -> int:
    ref = REF if REF != "main" else default_branch()
    url = f"https://codeload.github.com/{REPO}/tar.gz/{ref}"
    print(f"Downloading {REPO}@{ref} ...")
    blob = _get(url)
    DEST.mkdir(parents=True, exist_ok=True)
    n = 0
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        for m in tar.getmembers():
            # strip the top-level "<repo>-<ref>/" prefix
            parts = m.name.split("/", 1)
            if len(parts) < 2 or not parts[1]:
                continue
            rel = parts[1]
            if not rel.startswith("Data_and_Results/"):
                continue
            m.name = rel
            tar.extract(m, DEST)  # nosec: trusted academic repo
            if m.isfile():
                n += 1
    print(f"Extracted {n} files into {DEST}")
    human = DEST / "Data_and_Results" / "Human_Data"
    if human.exists():
        print("Human corpora present:")
        for d in sorted(p.name for p in human.iterdir() if p.is_dir()):
            print(f"  - {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
