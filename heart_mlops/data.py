"""Download, validate, and clean the UCI Cleveland data."""

import argparse
import hashlib
import json
import urllib.request

import pandas as pd

from heart_mlops.config import (
    CLEAN_PATH,
    FEATURES,
    RAW_COLUMNS,
    RAW_PATH,
    RAW_SHA256,
    SOURCE_URL,
    TARGET,
)


def download_raw(force: bool = False):
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    if RAW_PATH.exists() and not force:
        digest = hashlib.sha256(RAW_PATH.read_bytes()).hexdigest()
        if digest != RAW_SHA256:
            raise ValueError(f"Existing UCI file checksum changed: {digest}")
        return RAW_PATH
    with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:
        content = response.read()
    digest = hashlib.sha256(content).hexdigest()
    if digest != RAW_SHA256:
        raise ValueError(f"UCI download checksum changed: {digest}")
    RAW_PATH.write_bytes(content)
    return RAW_PATH


def load_raw(path=RAW_PATH):
    frame = pd.read_csv(path, header=None, names=RAW_COLUMNS, na_values="?")
    if frame.shape[1] != len(RAW_COLUMNS):
        raise ValueError("Expected 13 feature columns and one target column")
    return frame


def clean_data(frame: pd.DataFrame):
    if set(RAW_COLUMNS) - set(frame.columns):
        raise ValueError("Raw data has missing columns")
    cleaned = frame[RAW_COLUMNS].copy()
    for column in RAW_COLUMNS:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    target_values = cleaned["num"].dropna()
    if not (target_values.between(0, 4) & (target_values % 1 == 0)).all():
        raise ValueError("Target must be an integer from 0 to 4")
    before = len(cleaned)
    cleaned = cleaned.dropna(subset=RAW_COLUMNS).drop_duplicates().reset_index(drop=True)
    cleaned[TARGET] = (cleaned.pop("num") > 0).astype(int)
    cleaned = cleaned[[*FEATURES, TARGET]]
    summary = {
        "raw_rows": before,
        "clean_rows": len(cleaned),
        "removed_missing_or_duplicate_rows": before - len(cleaned),
        "negative_count": int((cleaned[TARGET] == 0).sum()),
        "positive_count": int((cleaned[TARGET] == 1).sum()),
        "raw_sha256": RAW_SHA256,
        "source": SOURCE_URL,
    }
    if cleaned.empty or cleaned[TARGET].nunique() != 2:
        raise ValueError("Cleaned data must contain both target classes")
    return cleaned, summary


def prepare_data(force_download: bool = False):
    path = download_raw(force_download)
    data, summary = clean_data(load_raw(path))
    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(CLEAN_PATH, index=False)
    (CLEAN_PATH.parent / "data_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return data, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()
    _, summary = prepare_data(args.force_download)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
