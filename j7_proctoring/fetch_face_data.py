"""Fetch the FairFace validation set (padding=1.25) for the J7 proctoring audit.

Source: Karkkainen & Joo (2021), "FairFace: Face Attribute Dataset for Balanced Race,
Gender, and Age for Bias Measurement and Mitigation", WACV. Distributed by the authors
at https://github.com/joojs/fairface; mirrored verbatim on the Hugging Face Hub as
HuggingFaceM4/FairFace. We pull the VALIDATION split of the padding=1.25 ("in the
wild" loose crop) configuration: 10,954 face images with perceived-race, gender, and
age-group labels assigned by the dataset authors.

Both the repository revision and the parquet shard name are pinned below, so a re-run
retrieves byte-identical data. Images are written to data/raw/fairface_val/ (gitignored,
large binaries); labels go to data/fairface_val_labels.csv with one row per image. Race
class names are read from the Hugging Face features metadata embedded in the parquet
file, not hardcoded.
"""

import io
import json
import os

import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

REPO_ID = "HuggingFaceM4/FairFace"
REVISION = "54d573cdb8b5af490ba8da9da2799628f6e5c496"  # pinned 2026-06-11
SHARD = "1.25/validation-00000-of-00001-09e3e67bb00ab4ec.parquet"

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "data", "raw", "fairface_val")
LABELS_CSV = os.path.join(HERE, "data", "fairface_val_labels.csv")


def class_names(parquet_path):
    """Read ClassLabel name lists from the huggingface metadata block."""
    meta = pq.read_schema(parquet_path).metadata
    info = json.loads(meta[b"huggingface"].decode("utf-8"))
    feats = info["info"]["features"]
    return {
        col: spec["names"]
        for col, spec in feats.items()
        if isinstance(spec, dict) and spec.get("_type") == "ClassLabel"
    }

def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    path = hf_hub_download(REPO_ID, SHARD, repo_type="dataset", revision=REVISION)
    names = class_names(path)
    table = pq.read_table(path)
    df = table.to_pandas()

    rows = []
    for i, rec in df.iterrows():
        img = rec["image"]  # struct {bytes, path}
        fname = os.path.basename(img["path"]) if img.get("path") else f"{i}.jpg"
        out = os.path.join(RAW_DIR, fname)
        if not os.path.exists(out):
            with open(out, "wb") as fh:
                fh.write(io.BytesIO(img["bytes"]).getvalue())
        row = {"file": fname}
        for col in df.columns:
            if col == "image":
                continue
            val = rec[col]
            if col in names:
                row[col] = names[col][int(val)]
            else:
                row[col] = val
        rows.append(row)

    labels = pd.DataFrame(rows)
    labels.to_csv(LABELS_CSV, index=False)
    print(f"wrote {len(labels)} images -> {RAW_DIR}")
    print(f"wrote labels -> {LABELS_CSV}")
    for col in names:
        print(f"\n{col} distribution:")
        print(labels[col].value_counts().to_string())

if __name__ == "__main__":
    main()
