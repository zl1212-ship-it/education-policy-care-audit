# J7 — The Camera That Cannot See Everyone

An algorithm audit of the face-detection step that remote-proctoring systems use to
decide whether an examinee is present. Online exams point a webcam at a student and
let a vision model confirm a face is there; "no face detected" becomes an absence or
integrity flag, a lockout, or an escalation to human review. If the detection step
sees darker faces worse, those students carry a higher risk of being falsely flagged
for the same behavior: sitting in front of their own camera.

Two layers:

1. **Detection layer (audit).** Every image in the panel contains exactly one face
   by dataset construction, so a "no face" return is always a miss. We run four open
   face detectors spanning the deployed spectrum (legacy Haar cascade, production
   YuNet, on-device MediaPipe BlazeFace, deep MTCNN) over the FairFace validation
   set and measure the miss rate by an image-derived skin-tone measure (ITA) and by
   the dataset's perceived-race labels, at native exposure and under controlled
   low-light degradation simulating dim webcam conditions.
2. **Consequence layer (mapping).** Public proctoring-vendor documentation is coded
   for how a face-detection failure becomes a consequence for the student (flag,
   lockout, instructor report), connecting the measured error gap to assessment
   access.

Middle-range claim: automated presence verification redistributes the burden of
being seen. A perception failure in the camera pipeline becomes an
assessment-access harm through the rules that treat "no face" as evidence of
absence or misconduct.

Honest scope limit (stated in the paper): commercial proctoring engines are closed;
the audit measures the open face-detection layer the same vision stack builds on,
plus the vendors' own public documentation for the consequence mapping. It does not
claim to measure any vendor's closed model directly.

## Pipeline
```
fetch_face_data.py    # FairFace validation set (padding=1.25), HF mirror, revision-pinned
build_face_panel.py   # + ITA skin-tone measure (CIELAB) and Del Bino tone bins -> data/face_panel.csv
run_detectors.py      # 4 open detectors x exposure conditions -> data/detection_outcomes.csv
analyze_detection.py  # miss rates by tone bin / race, contrasts, trend tests -> data/results_summary.csv
verify_identity.py    # (planned) LFW face-verification FNMR by skin tone
build_vendor_corpus.py# (planned) vendor doc consequence mapping, J6-style coded corpus
make_figures.py       # (planned) figures -> ../paper/blinded-manuscript/j7_figure*.{pdf,png}
```

## Data
- `data/fairface_val_labels.csv` — one row per image: FairFace age / gender / race labels.
- `data/face_panel.csv` — labels + ITA (degrees) + tone bin + skin-mask quality flag.
- `data/detection_outcomes.csv` — long: image x detector x exposure, faces found, top confidence, detected.
- `data/results_summary.csv` — per-stratum miss rates (Wilson CIs), darkest-vs-lightest and
  Black-vs-White contrasts (risk diff, fold ratio, Fisher exact), ITA trend.
- Raw images sit under `data/raw/` (gitignored); `fetch_face_data.py` re-creates them
  byte-identically from the pinned revision.

## Headline
**Detection layer (baseline: four open detectors, 10,954 FairFace validation faces,
native exposure).** Every image contains exactly one face, so every "no face" return
is a miss. The legacy webcam-grade detector (Haar cascade, 22.8% overall miss) misses
**30.2% of dark-bin faces vs 17.6% of very-light faces (1.71x, Fisher p = 5e-11)**
and **35.5% of Black-labeled vs 22.7% of White-labeled faces (1.56x, p = 4e-17)**;
the tone gradient is monotone from tan (15.7%) through brown (19.6%) to dark (30.2%)
and survives restriction to adults (1.58x / 1.61x). The modern detectors sit at the
ceiling at native exposure (MediaPipe 0.055% overall miss, MTCNN 0.44%; Black-White
gaps point the same way, MTCNN 2.1x, but are not significant at these near-zero
rates), which motivates the designed experiment: the low-light sweep (exposure 0.5
to 0.15 in linear-light space) measures where the seen/unseen boundary moves as the
webcam dims, the actual proctoring condition. YuNet (default score threshold 0.9,
9.5% overall miss) shows elevated misses at BOTH ITA tails but no Black-White gap,
evidence that photo exposure contaminates the very-light ITA tail; the
author-assigned race labels serve as the independent stratifier for exactly this
reason.

## Target journals
Computers & Education (primary); Internet and Higher Education; AI & Society.
