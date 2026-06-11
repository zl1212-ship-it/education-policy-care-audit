"""Face-verification (1:1) layer: genuine-pair rejection by skin tone on LFW.

Proctoring systems verify identity by comparing the exam-time webcam capture to an
enrollment photo (ExamID-style 1:1 match). The harm analog to "no face detected" is
the false non-match: the system decides you are not you. Estimand: the probability
that a GENUINE pair (two photos of the same person) is rejected, by the subject's
skin tone, at a decision threshold fixed where the verifier produces FMR = 1% on
impostor pairs at native exposure (an FRVT-style operating point, held fixed across
conditions; see analyze_verification.py).

Cascade honesty: a verifier first detects the face, then embeds and matches. If its
detector finds no face, identity cannot be confirmed at all. Detect failures and
match failures are recorded separately; the proctoring-relevant outcome is their
union ("cannot confirm identity").

Probe-side dimming: the enrollment image stays at native exposure; the probe image
is underexposed in linear-light space (run_detectors.underexpose). This matches the
deployment asymmetry: enrollment under good light, exam capture in a dim room.

Verifiers (open weights, pinned):
- facenet  MTCNN (facenet-pytorch) detect+align -> InceptionResnetV1 (VGGFace2),
           cosine similarity.
- sface    YuNet 2023mar detect -> SFace 2021dec (OpenCV model zoo,
           sha256-pinned), cosine similarity.

Data: LFW funneled + the authors' 10-fold pairs protocol (6,000 pairs: 3,000
genuine, 3,000 impostor; Huang et al. 2007). Files are fetched through
scikit-learn's checksummed downloader (tested on scikit-learn 1.6.1) but read
directly from disk here, pair by pair, to avoid materializing the full image
array. Skin tone: median ITA over the pair's two native-exposure images
(build_face_panel.ita_of; genuine pairs are one person). LFW skews light-skinned,
so the analysis uses within-sample terciles rather than absolute Del Bino bins.

Output: data/verification_outcomes.csv, one row per pair x verifier x exposure.
"""

import argparse
import os

import cv2
import numpy as np
import pandas as pd

from build_face_panel import ita_of
from run_detectors import (MODEL_DIR, YUNET_PATH, YUNET_SHA256, YUNET_URL,
                           fetch_model, underexpose)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(HERE, "data", "verification_outcomes.csv")

LFW_HOME = os.path.expanduser("~/scikit_learn_data/lfw_home")
PAIRS_TXT = os.path.join(LFW_HOME, "pairs.txt")
FUNNELED = os.path.join(LFW_HOME, "lfw_funneled")

SFACE_URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/"
             "face_recognition_sface/face_recognition_sface_2021dec.onnx")
SFACE_SHA256 = "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"
SFACE_PATH = os.path.join(MODEL_DIR, "face_recognition_sface_2021dec.onnx")

EXPOSURES = [1.0, 0.5, 0.35, 0.25, 0.15]
BATCH = 32


def ensure_lfw():
    if os.path.exists(PAIRS_TXT) and os.path.isdir(FUNNELED):
        return
    # checksummed download + extract only (no image-array build); private helper,
    # pinned to the scikit-learn 1.6.x layout
    from sklearn.datasets._lfw import _check_fetch_lfw
    _check_fetch_lfw(data_home=os.path.dirname(LFW_HOME), funneled=True,
                     download_if_missing=True)


def _path(name, num):
    return os.path.join(FUNNELED, name, f"{name}_{int(num):04d}.jpg")


def load_pairs():
    """Parse the authors' pairs.txt: per fold, 300 genuine then 300 impostor."""
    ensure_lfw()
    lines = open(PAIRS_TXT).read().strip().splitlines()
    n_folds, n_per = (int(x) for x in lines[0].split())
    rows, i = [], 1
    for fold in range(n_folds):
        for _ in range(n_per):
            name, a, b = lines[i].split(); i += 1
            rows.append((fold, 1, _path(name, a), _path(name, b)))
        for _ in range(n_per):
            n1, a, n2, b = lines[i].split(); i += 1
            rows.append((fold, 0, _path(n1, a), _path(n2, b)))
    df = pd.DataFrame(rows, columns=["fold", "genuine", "path_a", "path_b"])
    df.insert(0, "pair_idx", range(len(df)))
    return df


def load_bgr(path, exposure=1.0):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    return underexpose(img, exposure)


class FacenetVerifier:
    name = "facenet"
    dim = 512

    def __init__(self):
        import torch
        from facenet_pytorch import MTCNN, InceptionResnetV1
        self.torch = torch
        self.mtcnn = MTCNN(keep_all=False, device="cpu")
        self.resnet = InceptionResnetV1(pretrained="vggface2").eval()

    def embed_paths(self, paths, exposure=1.0):
        # MTCNN is called per image: facenet-pytorch's batched select_boxes
        # builds a ragged np.array when only some images in a batch have a
        # face, which numpy >= 1.24 rejects.
        out = np.full((len(paths), self.dim), np.nan, dtype=np.float32)
        with self.torch.no_grad():
            for s in range(0, len(paths), BATCH):
                kept = []
                for i, p in enumerate(paths[s:s + BATCH]):
                    img = cv2.cvtColor(load_bgr(p, exposure), cv2.COLOR_BGR2RGB)
                    crop = self.mtcnn(img)
                    if crop is not None:
                        kept.append((i, crop))
                if not kept:
                    continue
                idx, tensors = zip(*kept)
                emb = self.resnet(self.torch.stack(tensors)).numpy()
                out[np.array(idx) + s] = emb
        return out


class SfaceVerifier:
    name = "sface"
    dim = 128

    def __init__(self):
        self.det = cv2.FaceDetectorYN.create(
            fetch_model(YUNET_URL, YUNET_PATH, YUNET_SHA256), "", (250, 250))
        self.rec = cv2.FaceRecognizerSF.create(
            fetch_model(SFACE_URL, SFACE_PATH, SFACE_SHA256), "")

    def embed_paths(self, paths, exposure=1.0):
        out = np.full((len(paths), self.dim), np.nan, dtype=np.float32)
        for i, p in enumerate(paths):
            bgr = load_bgr(p, exposure)
            h, w = bgr.shape[:2]
            self.det.setInputSize((w, h))
            faces = self.det.detect(bgr)[1]
            if faces is None:
                continue
            top = faces[np.argmax(faces[:, -1])]
            crop = self.rec.alignCrop(bgr, top)
            out[i] = self.rec.feature(crop).ravel()
        return out


def cosine(a, b):
    num = (a * b).sum(axis=1)
    den = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)
    return num / den


def merge_save(rows):
    new = pd.DataFrame(rows)
    if os.path.exists(OUT_CSV):
        old = pd.read_csv(OUT_CSV)
        key = ["pair_idx", "verifier", "exposure"]
        keep = old.merge(new[key].drop_duplicates(), on=key, how="left",
                         indicator=True)
        old = old[keep["_merge"].values == "left_only"]
        new = pd.concat([old, new], ignore_index=True)
    new.sort_values(["verifier", "exposure", "pair_idx"]).to_csv(OUT_CSV,
                                                                 index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verifiers", default="sface,facenet")
    ap.add_argument("--exposures", default=",".join(str(e) for e in EXPOSURES))
    ap.add_argument("--limit", type=int, default=0, help="smoke-test on N pairs")
    args = ap.parse_args()
    exposures = [float(x) for x in args.exposures.split(",")]

    df = load_pairs()
    if args.limit:
        df = df.head(args.limit)

    ita_cache = {}
    def ita(path):
        if path not in ita_cache:
            ita_cache[path] = ita_of(load_bgr(path))[0]
        return ita_cache[path]
    ita_pair = np.array([np.median([ita(a), ita(b)])
                         for a, b in zip(df["path_a"], df["path_b"])])
    print(f"{len(df)} pairs, ITA computed", flush=True)

    builders = {"facenet": FacenetVerifier, "sface": SfaceVerifier}
    for vname in args.verifiers.split(","):
        ver = builders[vname]()
        emb_a = ver.embed_paths(df["path_a"].tolist())  # enrollment: native, once
        det_a = ~np.isnan(emb_a[:, 0])
        print(f"{vname}: enrollment detect rate {det_a.mean():.3%}", flush=True)
        for exp in exposures:
            emb_b = ver.embed_paths(df["path_b"].tolist(), exposure=exp)
            det_b = ~np.isnan(emb_b[:, 0])
            sim = cosine(emb_a, emb_b)
            rows = [{"pair_idx": int(df["pair_idx"].iloc[i]),
                     "fold": int(df["fold"].iloc[i]), "verifier": vname,
                     "exposure": exp, "genuine": int(df["genuine"].iloc[i]),
                     "ita_pair": round(float(ita_pair[i]), 2),
                     "detect_enroll": int(det_a[i]),
                     "detect_probe": int(det_b[i]),
                     "similarity": np.nan if np.isnan(sim[i])
                     else round(float(sim[i]), 5)}
                    for i in range(len(df))]
            merge_save(rows)
            print(f"done {vname} exp={exp}: probe detect {det_b.mean():.3%}",
                  flush=True)

if __name__ == "__main__":
    main()
