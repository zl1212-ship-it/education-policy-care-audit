"""Assemble the J7 face panel: FairFace labels + an image-derived skin-tone measure.

Skin tone is measured as the Individual Typology Angle (ITA; Chardon, Cretois &
Hourseau 1991), the standard dermatological colorimetry index: ITA = arctan((L* - 50)
/ b*) in degrees, computed in CIELAB over skin pixels. Higher ITA = lighter skin. ITA
is mapped to the six Del Bino & Bernerd (2013) tone categories (very light, light,
intermediate, tan, brown, dark), which parallel the Fitzpatrick I-VI ordering used by
Gender Shades (Buolamwini & Gelbru 2018).

Measurement notes (stated here because the audit depends on them):
- ITA is computed from the dataset-provided face crop (FairFace localizes every face
  with its own pipeline at construction time), so the tone measure does NOT depend on
  any detector audited in run_detectors.py. There is no circularity between the
  stratifier and the outcome.
- Skin pixels are selected inside a fixed central window of the padding=1.25 crop
  (the face occupies the center by construction) with a standard YCrCb skin filter
  (Cr in [133,173], Cb in [77,127]); if fewer than 200 pixels survive the filter, the
  unfiltered central window is used and the row is flagged (skin_filter_ok=0).
- The perceived-race label is FairFace's, kept as a second, independent stratifier;
  the analysis reports both and their agreement (Black-labeled faces should sit at
  the dark end of ITA, which the crosstab printed at build time verifies).
- The Del Bino thresholds were calibrated on colorimeter readings under controlled
  illumination; ITA computed from uncalibrated web photographs is shifted toward the
  dark end (the build printout shows the shift). The bins are therefore a RELATIVE
  ordering of the sample, not a dermatological diagnosis of any subject, and every
  analysis is replicated on the author-assigned race labels as the independent check.

Output: data/face_panel.csv, one row per image.
"""

import os

import cv2
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "data", "raw", "fairface_val")
LABELS_CSV = os.path.join(HERE, "data", "fairface_val_labels.csv")
PANEL_CSV = os.path.join(HERE, "data", "face_panel.csv")

# central window of the padding=1.25 crop (x0, x1, y0, y1 as fractions)
WINDOW = (0.34, 0.66, 0.30, 0.62)
MIN_SKIN_PX = 200

# Del Bino & Bernerd (2013) ITA thresholds, degrees
TONE_BINS = [
    (55.0, np.inf, "very_light"),
    (41.0, 55.0, "light"),
    (28.0, 41.0, "intermediate"),
    (10.0, 28.0, "tan"),
    (-30.0, 10.0, "brown"),
    (-np.inf, -30.0, "dark"),
]


def ita_of(img_bgr):
    """Median ITA (degrees) over skin pixels in the central window."""
    h, w = img_bgr.shape[:2]
    x0, x1, y0, y1 = WINDOW
    patch = img_bgr[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]

    ycrcb = cv2.cvtColor(patch, cv2.COLOR_BGR2YCrCb)
    cr, cb = ycrcb[:, :, 1], ycrcb[:, :, 2]
    skin = (cr >= 133) & (cr <= 173) & (cb >= 77) & (cb <= 127)
    ok = int(skin.sum() >= MIN_SKIN_PX)

    lab = cv2.cvtColor(patch, cv2.COLOR_BGR2LAB).astype(np.float64)
    L = lab[:, :, 0] * 100.0 / 255.0
    b = lab[:, :, 2] - 128.0
    if ok:
        L, b = L[skin], b[skin]
    ita = np.degrees(np.arctan2(L - 50.0, b))
    return float(np.median(ita)), ok


def tone_bin(ita):
    for lo, hi, name in TONE_BINS:
        if lo <= ita < hi or (hi is np.inf and ita >= lo):
            return name
    return "dark"


def main():
    labels = pd.read_csv(LABELS_CSV)
    itas, oks = [], []
    for fname in labels["file"]:
        img = cv2.imread(os.path.join(RAW_DIR, fname))
        ita, ok = ita_of(img)
        itas.append(ita)
        oks.append(ok)

    panel = labels.copy()
    panel["ita"] = np.round(itas, 2)
    panel["tone_bin"] = [tone_bin(v) for v in itas]
    panel["skin_filter_ok"] = oks
    panel.to_csv(PANEL_CSV, index=False)

    order = [name for _, _, name in TONE_BINS]
    panel["tone_bin"] = pd.Categorical(panel["tone_bin"], order, ordered=True)
    print(f"wrote {len(panel)} rows -> {PANEL_CSV}")
    print(f"skin filter ok: {panel['skin_filter_ok'].mean():.1%}")
    print("\ntone_bin counts:")
    print(panel["tone_bin"].value_counts().reindex(order).to_string())
    print("\nmedian ITA by race (validity check, expect Black lowest):")
    print(panel.groupby("race")["ita"].median().sort_values().to_string())
    print("\ntone_bin x race crosstab:")
    print(pd.crosstab(panel["tone_bin"], panel["race"]).to_string())

if __name__ == "__main__":
    main()
