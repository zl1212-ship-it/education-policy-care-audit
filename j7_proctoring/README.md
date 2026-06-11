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
verify_identity.py    # LFW 1:1 verification (MTCNN+FaceNet, YuNet+SFace), probe-side dimming
analyze_verification.py # FNMR / cannot-verify by ITA tercile at fixed FMR -> data/verification_results.csv
build_vendor_corpus.py# fetch + archive vendor documentation (registry-driven, provenance headers)
analyze_vendor.py     # consequence codes + detection-layer bridge -> data/vendor_results.csv
make_figures.py       # (planned) figures -> ../paper/blinded-manuscript/j7_figure*.{pdf,png}
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
  access date is the evidence of record behind each code (same rule as J6 policy_raw).
- `data/vendor_corpus.csv` — one row per vendor, six codes per `CODEBOOK_vendor.md`, each
  with a verbatim support passage and source slug.
- `data/vendor_results.csv` — code distributions + the mechanical bridge from measured
  miss-rate ratios to implied per-check flag-rate ratios.
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

**Low-light sweep (exposure 0.5 -> 0.15, linear-light).** Dimming amplifies the
disparity in three of the four detectors, on the race contrast that the ITA
contamination cannot touch. Haar: Black miss rises 35.5% -> 42.6% while White rises
22.7% -> 25.9% (risk difference 12.8pp -> 16.7pp, p = 6e-26). YuNet: the Black-White
ratio climbs monotonically with darkness, 1.04 -> 1.12 -> 1.14 -> 1.16 -> 1.25
(p = 0.002 at 0.15; adults 1.09 -> 1.30, p = 0.001). MTCNN leaves the ceiling and a
significant gap emerges: 0.71% vs 0.34% (n.s.) at native exposure becomes 4.6% vs
2.4% (1.9x, p = 4e-4) at 0.15. So equal-light parity is not equal-dark parity: the
gap appears exactly under the deployed condition, a dim room behind a webcam.
MediaPipe stays at the ceiling throughout; pure exposure scaling is largely undone
by its input normalization (stated limitation: real low light also adds sensor
noise, so these sweep numbers are conservative). The very-light ITA tail degrades
fastest among modern detectors when dimmed, consistent with that tail holding
overexposed, low-contrast photos rather than the lightest-skinned subjects.

**Verification layer (LFW 10-fold pairs, 3,000 genuine / 3,000 impostor, two open
cascades, threshold fixed at FMR = 1% on native-exposure impostors).** The matcher
does not reproduce the detection gap: genuine-pair rejection ("you are not you")
is flat across ITA terciles for both stacks at every exposure (FaceNet 5.6% vs
5.3% darkest-vs-lightest at native, 1.06x, p = 0.8; SFace 3.2% vs 3.0%, 1.06x,
p = 0.9; all dimmed conditions 0.94x-1.10x, every p > 0.4; Spearman ITA-match
|rho| < 0.013 throughout). Probe-side dimming does not open a gap either, and the
cascades' internal detectors almost never fail on LFW's tight well-lit crops
(99.98% detect at exposure 0.15), so cannot-verify collapses to the match decision
there. Within open stacks, the skin-tone burden concentrates at the presence-
detection gate measured on in-the-wild images, not the identity matcher: precisely
the step proctoring systems automate as the "no face detected" flag. Bounded by
LFW's light-skewed composition (within-sample terciles, no race labels), stated in
the paper.

**Consequence layer (five vendor product lines, coded from archived vendor-authored
documentation).** Four of five document an automatic event when no face is detected
(Proctorio "if the test-taker has left the exam for any reason"; Respondus
"warn[s] students when their face cannot be detected"; Honorlock "AI will flag the
incident"; ExamSoft's "Applicant Missing" incident category), so for those four the
per-check flag-rate ratio is mechanically the detector's miss-rate ratio measured
above. All five document a human in the loop, but for four of five the terminal
reviewer is the instructor: the skewed flag is not filtered out, it is delivered to
the grader as a suspicion record. None of the archived pages acknowledges that face
detection can perform differently by skin tone; the two that address the bias
controversy at all (Proctorio, Honorlock) deflect by distinguishing detection from
recognition, which is nonresponsive here because the measured gap sits in detection
itself. Two vendors (Respondus, ExamSoft) instruct students to secure lighting
("Turn on lights to illuminate your face"), conceding the mechanism the exposure
sweep manipulates while assigning the remedy to the student; the sweep shows the
remedy does not equalize, because at any fixed dimness darker faces fail first.

## Target journals
Computers & Education (primary); Internet and Higher Education; AI & Society.
