# Face-detection and face-verification benchmark data

Builds a face-image panel with a per-image skin-tone measure and records per-image
outcomes for four open face detectors and two open 1:1 face-verification cascades,
at native exposure and under controlled exposure changes. A registry of public
documentation pages and a fetcher for them are included.

## Run order
```
fetch_face_data.py      # FairFace validation set (padding=1.25), Hugging Face mirror, pinned revision -> data/fairface_val_labels.csv
build_face_panel.py     # adds the ITA skin-tone measure (CIELAB) and Del Bino tone bins -> data/face_panel.csv
run_detectors.py        # 4 open detectors x exposure conditions -> data/detection_outcomes.csv
verify_identity.py      # LFW 1:1 pairs, 2 open verifier cascades, probe-side dimming -> data/verification_outcomes.csv
build_vendor_corpus.py  # fetches the pages listed in data/vendor_registry.csv -> data/vendor_raw/ (not committed)
```

## Data
- `data/fairface_val_labels.csv`: one row per image: FairFace age, gender, and race labels.
- `data/face_panel.csv`: labels plus ITA (degrees), tone bin, and a skin-mask quality flag.
- `data/detection_outcomes.csv`: long format: image x detector x exposure, faces found, top confidence, detected.
- `data/verification_outcomes.csv`: long format: LFW pair x verifier x exposure, detect flags for
  both images, cosine similarity.
- `data/vendor_registry.csv`: public documentation URLs read by `build_vendor_corpus.py`.
- FairFace images (`data/raw/`, pinned revision) and the YuNet, BlazeFace, and SFace weights
  (`models/`, sha256-checked) are not committed; the scripts download them. LFW is cached by
  scikit-learn under `~/scikit_learn_data/`, facenet-pytorch supplies the MTCNN and
  InceptionResnetV1 weights, and the Haar cascade ships with opencv-python.

## Options
- `run_detectors.py --exposures 1.0,0.5,0.35,0.25,0.15`: exposure levels (linear-light scaling)
- `run_detectors.py --detectors haar3,haar8,yunet06`: Haar at minNeighbors 3 and 8, YuNet at score threshold 0.6
- `run_detectors.py --noise --exposures 0.25,0.15`: Poisson and Gaussian sensor noise after dimming
- `run_detectors.py --small-face 0.2`: face shrunk to 20% of the frame

Extra Python packages: opencv-python, mediapipe, torch, facenet-pytorch, huggingface_hub,
pyarrow, scikit-learn (1.6.x, for the LFW download).
