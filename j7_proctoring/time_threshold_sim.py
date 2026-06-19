"""Does the temporal step (per-frame to per-session) overturn the racial gap?

The detection audit measures a per-image miss rate: the probability a detector
returns "no face" on one still image. A deployed proctoring tool watches a video
stream and raises a "no face" event only after the face is undetected for a
sustained window (it cannot flag on a single dropped frame, or it would flag
everyone). So the per-image rate is not directly a per-session flag rate. This
script tests whether that temporal aggregation changes the racial conclusion.

Model. A session lasts T seconds sampled at f frames per second (N = T*f frames).
For a given student the per-frame detection state is a two-state Markov chain
(detected / undetected) with stationary miss probability p set to the measured
per-image miss rate for that student's group, and lag-1 autocorrelation rho of the
miss indicator:
    P(miss | miss)   = p + (1 - p) * rho
    P(miss | detect) = p * (1 - rho)
rho = 0 makes frames independent (a face flickers in and out at random); rho -> 1
makes detectability a fixed property of the (face, lighting) pair for the session,
the realistic case, since a darker face in a dim room is persistently, not randomly,
hard to find. A "no face" event fires when the face is undetected for a continuous
window of at least w seconds (k = w*f consecutive missed frames).

Identification / honesty. This is a SIMULATION on top of the measured per-frame
rates, not a measurement of any deployed tool; FairFace has one image per face, so
the within-session correlation rho cannot be estimated from the data and is instead
swept across its full range. The question is only whether the per-session flag-rate
ratio (Black vs White) survives the temporal step. p values are read from the
measured Haar race rates (analyze_detection.py / results_summary.csv equivalent).

Output: data/results_time_threshold.csv. Reproducible (seeded).
"""

import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL_CSV = os.path.join(HERE, "data", "face_panel.csv")
OUTCOMES_CSV = os.path.join(HERE, "data", "detection_outcomes.csv")
OUT_CSV = os.path.join(HERE, "data", "results_time_threshold.csv")

SEED = 20260615
N_SESSIONS = 40000
FPS = 1                  # snapshot-style sampling; continuous video has more frames
                         # per second, which only makes sustained runs more likely.
T_SECONDS = 60           # a one-minute monitoring window. Over a full exam the
                         # sustained-gap probability saturates toward one for both
                         # groups (the tool flags nearly everyone, a mass false-flag
                         # regime), so a per-minute window is the interpretable unit
                         # for the racial ratio.
RHOS = [0.0, 0.9, 0.99, 0.999]      # frame-to-frame persistence of detection state
WINDOWS = [3, 5, 10]                # sustained "no face" threshold, seconds
EXPOSURES = [1.0, 0.15]


def measured_haar_rate(d, exposure, race):
    g = d[(d["detector"] == "haar") & (d["exposure"] == exposure)
          & (d["race"] == race)]
    return 1 - g["detected"].mean()


def flag_rate(p, rho, k, n_frames, n_sessions, rng):
    """Monte Carlo P(a session has a run of >= k consecutive misses)."""
    p_mm = p + (1 - p) * rho        # P(miss | previous miss)
    p_dm = p * (1 - rho)            # P(miss | previous detect)
    state = rng.random(n_sessions) < p        # frame 0, stationary
    run = np.where(state, 1, 0)
    flagged = run >= k
    for _ in range(1, n_frames):
        thresh = np.where(state, p_mm, p_dm)
        state = rng.random(n_sessions) < thresh
        run = np.where(state, run + 1, 0)
        flagged |= run >= k
    return flagged.mean()


def main():
    panel = pd.read_csv(PANEL_CSV)
    outcomes = pd.read_csv(OUTCOMES_CSV)
    d = outcomes.merge(panel, on="file", how="left")

    n_frames = T_SECONDS * FPS
    rng = np.random.default_rng(SEED)
    rows = []
    for exp in EXPOSURES:
        p_black = measured_haar_rate(d, exp, "Black")
        p_white = measured_haar_rate(d, exp, "White")
        frame_ratio = p_black / p_white
        for rho in RHOS:
            for w in WINDOWS:
                k = w * FPS
                fb = flag_rate(p_black, rho, k, n_frames, N_SESSIONS, rng)
                fw = flag_rate(p_white, rho, k, n_frames, N_SESSIONS, rng)
                ratio = fb / fw if fw > 0 else np.inf
                rows.append({"detector": "haar", "exposure": exp,
                             "p_black_frame": round(p_black, 4),
                             "p_white_frame": round(p_white, 4),
                             "frame_miss_ratio": round(frame_ratio, 3),
                             "rho": rho, "window_s": w,
                             "flag_black": round(fb, 4), "flag_white": round(fw, 4),
                             "flag_ratio": round(ratio, 2)})

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)
    print(f"wrote {len(out)} rows -> {OUT_CSV}\n")

    for exp in EXPOSURES:
        sub = out[out["exposure"] == exp]
        fr = sub["frame_miss_ratio"].iloc[0]
        print(f"=== Haar, exposure={exp}: per-frame Black/White miss ratio = {fr} "
              f"(p_B={sub['p_black_frame'].iloc[0]}, p_W={sub['p_white_frame'].iloc[0]}) ===")
        print(sub[["rho", "window_s", "flag_black", "flag_white",
                   "flag_ratio"]].to_string(index=False))
        print()
    # the rho -> 1 analytic limit: flag rate -> p, ratio -> per-frame ratio
    print("Analytic persistence limit (rho -> 1): per-session flag rate -> per-frame "
          "miss rate, so flag ratio -> the per-frame miss ratio above.")


if __name__ == "__main__":
    main()
