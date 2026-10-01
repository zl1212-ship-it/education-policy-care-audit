# Sources

## Face images
- **FairFace** (Karkkainen & Joo, 2021, WACV): validation split, padding=1.25, 10,954
  images with the dataset authors' perceived race, gender, and age-group labels.
  Authors' distribution: https://github.com/joojs/fairface. Pulled from the Hugging Face
  mirror `HuggingFaceM4/FairFace` at the revision pinned in `fetch_face_data.py`.
  License: CC BY 4.0.
  - Karkkainen, K., & Joo, J. (2021). FairFace: Face attribute dataset for balanced race,
    gender, and age for bias measurement and mitigation. WACV 2021.
- **LFW** (Huang et al., 2007): funneled images and the 10-fold pairs protocol (3,000
  genuine and 3,000 impostor pairs), fetched through scikit-learn's checksummed
  downloader in `verify_identity.py`.

## Skin-tone measure
- Individual Typology Angle (ITA; Chardon, Cretois & Hourseau, 1991), computed per image
  in `build_face_panel.py` (CIELAB over a YCrCb skin mask). Tone categories follow
  Del Bino & Bernerd (2013).

## Open face detectors and verifiers
- **OpenCV Haar cascade**: `haarcascade_frontalface_default.xml` as shipped in opencv-python.
- **YuNet 2023mar**: OpenCV model zoo ONNX, sha256-pinned. https://github.com/opencv/opencv_zoo
- **MediaPipe BlazeFace short-range**: versioned model URL (`float16/1`), sha256-pinned.
- **MTCNN**: facenet-pytorch implementation (Zhang et al., 2016), default weights.
- **Verifiers**: facenet-pytorch InceptionResnetV1 (VGGFace2 weights) after MTCNN
  alignment; OpenCV SFace 2021dec (sha256-pinned) after YuNet detection.
- Score thresholds are library defaults unless a script option sets them. The Haar cascade
  has no score threshold; it runs with scaleFactor 1.1, minNeighbors 5, and a 30 x 30 pixel
  minimum face size.

## Documentation pages
- Public help-center, FAQ, and product pages listed in `data/vendor_registry.csv` (one URL
  and document type per row). `build_vendor_corpus.py` fetches them with a provenance
  header (URL, access date, HTTP status, raw-HTML sha256).
