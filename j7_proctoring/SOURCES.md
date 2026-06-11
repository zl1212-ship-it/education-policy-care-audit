# J7 sources and provenance

## Face image panel (anchor)
- **FairFace** (Karkkainen & Joo, 2021, WACV) — validation split, padding=1.25 ("in
  the wild" loose crop), 10,954 images with author-assigned perceived race, gender,
  and age group. Authors' distribution: https://github.com/joojs/fairface. Pulled
  from the verbatim Hugging Face mirror `HuggingFaceM4/FairFace`, revision pinned in
  `fetch_face_data.py` (`54d573cd...`). License CC BY 4.0.
  - Paper: Karkkainen, K., & Joo, J. (2021). FairFace: Face attribute dataset for
    balanced race, gender, and age for bias measurement and mitigation. WACV 2021.
- **Skin-tone measure**: Individual Typology Angle (ITA) computed per image in
  `build_face_panel.py` (CIELAB, YCrCb skin mask); categories per Del Bino & Bernerd
  (2013); ordering parallels Fitzpatrick I-VI as used by Gender Shades.
- **Verification layer (planned)**: LFW (Huang et al., 2007), public and
  identity-labeled, for FNMR-by-tone with the standard pairs protocol.

## Open face detectors (weights pinned in run_detectors.py)
- **OpenCV Haar cascade** — `haarcascade_frontalface_default.xml` as shipped in
  opencv-python (Viola-Jones 2001 family; the legacy webcam-grade detector).
- **YuNet 2023mar** — OpenCV model zoo ONNX, sha256-pinned
  (`8f2383e4...`). https://github.com/opencv/opencv_zoo
- **MediaPipe BlazeFace short-range** — Google on-device webcam detector,
  versioned URL (`float16/1`), sha256-pinned (`b4578f35...`).
- **MTCNN** — facenet-pytorch implementation (Zhang et al., 2016), default weights.
  All thresholds are library defaults, stated inline in `run_detectors.py`.

## Proctoring consequence mapping (vendor documentation layer)
- Public vendor documentation and help-center pages describing how face-detection /
  identity-verification outcomes become flags or lockouts (Proctorio, Respondus
  Monitor, Honorlock, ProctorU/Meazure, ExamSoft ExamID/ExamMonitor). Each entry will
  record URL + access date in provenance columns when this layer is built.

## Prior work this paper extends (not replicates)
- Buolamwini, J., & Gebru, T. (2018). Gender Shades. FAccT/PMLR — established
  commercial face-analysis error gaps by skin tone (classification, not the
  proctoring detection step).
- Karkkainen & Joo (2021) — FairFace dataset paper.
- Reports of proctoring face-detection failures for darker-skinned students
  (e.g., the 2020-21 bar-exam and university ExamSoft/Proctorio coverage; Feathers,
  "Proctorio Is Using Racist Algorithms to Detect Faces," Vice/Motherboard 2021,
  which tested one vendor's open-source dependency). J7's contribution: a
  reproducible multi-detector audit on a balanced labeled panel, a controlled
  low-light exposure design, and the education-assessment consequence mapping.
