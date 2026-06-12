# J7 — Remote-proctoring face-detection audit

Benchmarks the face-detection step used by remote-proctoring presence checks. Three
coordinated pipelines:

1. **Detection layer.** Four open face detectors (legacy Haar cascade, YuNet,
   MediaPipe BlazeFace, MTCNN) are run over the FairFace validation set, where
   every image contains exactly one face, so a "no face" return is always a miss.
   Miss rates are stratified by an image-derived skin-tone measure (ITA) and by
   the dataset's perceived-race labels, at native exposure and under controlled
   low-light degradation.
2. **Verification layer.** Two open 1:1 matcher cascades are benchmarked on LFW
   pairs with probe-side dimming, separating the presence-detection gate from the
   identity matcher.
3. **Consequence layer.** Archived public proctoring-vendor documentation is coded
   (protocol in `CODEBOOK_vendor.md`) for how a face-detection failure is handled
   (flag, lockout, escalation, human review).

Scope note: commercial proctoring engines are closed; the pipelines measure open
face-detection components and the vendors' own public documentation, not any
vendor's closed model.

## Pipeline
```
fetch_face_data.py    # FairFace validation set (padding=1.25), HF mirror, revision-pinned
build_face_panel.py   # + ITA skin-tone measure (CIELAB) and Del Bino tone bins -> data/face_panel.csv
run_detectors.py      # 4 open detectors x exposure conditions -> data/detection_outcomes.csv
analyze_detection.py  # miss rates by tone bin / race, contrasts, trend tests -> data/results_summary.csv
verify_identity.py    # LFW 1:1 verification (MTCNN+FaceNet, YuNet+SFace), probe-side dimming
analyze_verification.py # FNMR / cannot-verify by ITA tercile at fixed FMR -> data/verification_results.csv
build_vendor_corpus.py# fetch + archive vendor documentation (registry-driven, provenance headers)
analyze_vendor.py     # consequence codes + detection-layer bridge -> data/vendor_results.csv
make_figures.py       # Figures 1-3 -> ../paper/blinded-manuscript/j7_figure{1,2,3}.{pdf,png,tiff}
```

## Data
- `data/fairface_val_labels.csv` — one row per image: FairFace age / gender / race labels.
- `data/face_panel.csv` — labels + ITA (degrees) + tone bin + skin-mask quality flag.
- `data/detection_outcomes.csv` — long: image x detector x exposure, faces found, top confidence, detected.
- `data/results_summary.csv` — per-stratum miss rates (Wilson CIs), darkest-vs-lightest and
  Black-vs-White contrasts (risk diff, fold ratio, Fisher exact), ITA trend.
- `data/verification_outcomes.csv` — long: LFW pair x verifier x exposure, cascade detect
  flags + cosine similarity (enrollment side native, probe side dimmed).
- `data/verification_results.csv` — FNMR and cannot-verify rates by ITA tercile at the
  FMR=1% (and 0.1%) operating point, with contrasts and trend.
- `data/vendor_registry.csv` — curated vendor-authored public documentation URLs (five
  product lines: Proctorio, Respondus Monitor, Honorlock, ProctorU/Meazure, ExamSoft).
- `data/vendor_raw/` — archived page text with provenance headers (URL, access date,
  HTTP status, raw-HTML sha256). Committed: live pages change, so the stored text at the
  access date is the evidence of record behind each code.
- `data/vendor_corpus.csv` — one row per vendor, six codes per `CODEBOOK_vendor.md`, each
  with a verbatim support passage and source slug.
- `data/vendor_results.csv` — code distributions + the mechanical bridge from measured
  miss-rate ratios to implied per-check flag-rate ratios.
- Raw images sit under `data/raw/` (gitignored); `fetch_face_data.py` re-creates them
  byte-identically from the pinned revision.

## Optional robustness runs
- `run_detectors.py --detectors haar3,haar8` — Haar `minNeighbors` bracket around the default
- `run_detectors.py --noise --exposures 0.25,0.15` — Poisson + Gaussian sensor-noise conditions
