"""Run open-source face detectors over the FairFace panel; record no-face outcomes.

This is the measurement core of J7. Remote-proctoring systems gate exam access and
raise integrity flags on a face-detection step ("no face detected" / "could not
verify presence"). Commercial engines are closed, so the audit runs the open
detector families that the same computer-vision stack is built from, spanning the
deployed spectrum:

- haar       OpenCV Haar cascade (Viola-Jones), the legacy webcam-grade detector
             (haarcascade_frontalface_default.xml shipped with opencv-python).
- yunet      YuNet (2023mar ONNX from the OpenCV model zoo), a current lightweight
             production detector; weights sha256-verified below.
- mediapipe  MediaPipe/BlazeFace short-range model (model_selection=0), Google's
             on-device detector family designed for selfie/webcam video.
- mtcnn      MTCNN (facenet-pytorch implementation), the standard deep cascade used
             in face-verification pipelines.

Outcome per image x detector x exposure: number of faces found, top confidence, and
detected (1 if at least one face). Every image in the panel contains exactly one
face by dataset construction, so detected=0 is always a miss (a would-be "no face"
flag), never a correct rejection.

Low-light simulation: webcam underexposure is simulated by scaling image intensity
in LINEAR-LIGHT space (sRGB decoded with gamma 2.2, scaled by the exposure factor,
re-encoded), which approximates reducing scene illumination rather than editing
gamma-encoded pixels. exposure=1.0 is the unmodified image.

Detector thresholds are library defaults (stated inline); analyze_detection.py
checks sensitivity. Usage:
    python3 run_detectors.py                      # all detectors, exposure 1.0
    python3 run_detectors.py --exposures 1.0,0.5,0.35,0.25,0.15
    python3 run_detectors.py --detectors yunet,mediapipe

Results merge into data/detection_outcomes.csv (re-runs overwrite matching
file/detector/exposure rows, so the sweep can be extended incrementally).
"""

import argparse
import hashlib
import os
import urllib.request

import cv2
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "data", "raw", "fairface_val")
PANEL_CSV = os.path.join(HERE, "data", "face_panel.csv")
OUT_CSV = os.path.join(HERE, "data", "detection_outcomes.csv")
MODEL_DIR = os.path.join(HERE, "models")

YUNET_URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/"
             "face_detection_yunet/face_detection_yunet_2023mar.onnx")
YUNET_SHA256 = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"
YUNET_PATH = os.path.join(MODEL_DIR, "face_detection_yunet_2023mar.onnx")

BLAZE_URL = ("https://storage.googleapis.com/mediapipe-models/face_detector/"
             "blaze_face_short_range/float16/1/blaze_face_short_range.tflite")
BLAZE_SHA256 = "b4578f35940bf5a1a655214a1cce5cab13eba73c1297cd78e1a04c2380b0152f"
BLAZE_PATH = os.path.join(MODEL_DIR, "blaze_face_short_range.tflite")

GAMMA = 2.2


def fetch_model(url, path, sha256):
    os.makedirs(MODEL_DIR, exist_ok=True)
    if not os.path.exists(path):
        urllib.request.urlretrieve(url, path)
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if digest != sha256:
        raise RuntimeError(f"{os.path.basename(path)} sha256 mismatch: {digest}")
    return path


def underexpose(img_bgr, factor):
    """Scale intensity in linear-light space; factor=1.0 returns the input."""
    if factor >= 1.0:
        return img_bgr
    lin = np.power(img_bgr.astype(np.float32) / 255.0, GAMMA)
    out = np.power(lin * factor, 1.0 / GAMMA) * 255.0
    return np.clip(out, 0, 255).astype(np.uint8)


def det_haar(min_neighbors=5):
    casc = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    def run(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # OpenCV tutorial defaults: scaleFactor=1.1, minNeighbors=5. Lowering
        # minNeighbors is the Haar confidence dial: it accepts detections backed
        # by fewer overlapping neighbor windows, so it raises the detection rate.
        faces = casc.detectMultiScale(gray, 1.1, min_neighbors, minSize=(30, 30))
        return len(faces), np.nan
    return run


def det_yunet(score_threshold=None):
    args = {} if score_threshold is None else {"score_threshold": score_threshold}
    det = cv2.FaceDetectorYN.create(
        fetch_model(YUNET_URL, YUNET_PATH, YUNET_SHA256), "", (320, 320), **args)
    # library defaults: score_threshold=0.9, nms_threshold=0.3

    def run(img):
        h, w = img.shape[:2]
        det.setInputSize((w, h))
        faces = det.detect(img)[1]
        if faces is None:
            return 0, np.nan
        return len(faces), float(np.max(faces[:, -1]))
    return run


def det_mediapipe():
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision
    opts = vision.FaceDetectorOptions(
        base_options=BaseOptions(
            model_asset_path=fetch_model(BLAZE_URL, BLAZE_PATH, BLAZE_SHA256)),
        min_detection_confidence=0.5)  # library default
    fd = vision.FaceDetector.create_from_options(opts)

    def run(img):
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB,
                          data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        res = fd.detect(mp_img)
        if not res.detections:
            return 0, np.nan
        return (len(res.detections),
                float(max(d.categories[0].score for d in res.detections)))
    return run


def det_mtcnn():
    from facenet_pytorch import MTCNN
    mtcnn = MTCNN(keep_all=True, device="cpu")  # default thresholds .6/.7/.7

    def run(img):
        boxes, probs = mtcnn.detect(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if boxes is None:
            return 0, np.nan
        return len(boxes), float(np.max(probs))
    return run


BUILDERS = {"yunet": det_yunet, "mediapipe": det_mediapipe,
            "haar": det_haar, "mtcnn": det_mtcnn,
            # threshold-sensitivity variant: same YuNet weights at the looser
            # 0.6 operating point some deployments use (default is 0.9)
            "yunet06": lambda: det_yunet(score_threshold=0.6),
            # Haar confidence-dial sensitivity: minNeighbors 3 (looser) and 8
            # (stricter) bracket the default 5, to test whether the skin-tone gap
            # is an artifact of the operating point rather than the detector
            "haar3": lambda: det_haar(min_neighbors=3),
            "haar8": lambda: det_haar(min_neighbors=8)}


def merge_save(rows):
    new = pd.DataFrame(rows)
    if os.path.exists(OUT_CSV):
        old = pd.read_csv(OUT_CSV)
        key = ["file", "detector", "exposure"]
        keep = old.merge(new[key].drop_duplicates(), on=key, how="left",
                         indicator=True)
        old = old[keep["_merge"].values == "left_only"]
        new = pd.concat([old, new], ignore_index=True)
    new.sort_values(["detector", "exposure", "file"]).to_csv(OUT_CSV, index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detectors", default=",".join(BUILDERS))
    ap.add_argument("--exposures", default="1.0")
    args = ap.parse_args()
    detectors = args.detectors.split(",")
    exposures = [float(x) for x in args.exposures.split(",")]

    files = pd.read_csv(PANEL_CSV)["file"].tolist()
    for name in detectors:
        run = BUILDERS[name]()
        for exp in exposures:
            rows = []
            for i, fname in enumerate(files):
                img = underexpose(cv2.imread(os.path.join(RAW_DIR, fname)), exp)
                n, conf = run(img)
                rows.append({"file": fname, "detector": name, "exposure": exp,
                             "n_faces": n, "max_conf": np.nan if np.isnan(conf)
                             else round(conf, 4), "detected": int(n > 0)})
                if (i + 1) % 2000 == 0:
                    print(f"{name} exp={exp}: {i + 1}/{len(files)}", flush=True)
            merge_save(rows)
            miss = 1.0 - np.mean([r["detected"] for r in rows])
            print(f"done {name} exp={exp}: miss rate {miss:.3%}", flush=True)

if __name__ == "__main__":
    main()
