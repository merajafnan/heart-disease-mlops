import pytest

from heart_mlops.config import FEATURES, TARGET
from heart_mlops.data import clean_data


def test_cleaning_removes_missing_row_and_binarizes_target(sample_raw):
    cleaned, summary = clean_data(sample_raw)
    assert len(cleaned) == 2
    assert list(cleaned.columns) == [*FEATURES, TARGET]
    assert cleaned[TARGET].tolist() == [0, 1]
    assert summary["removed_missing_or_duplicate_rows"] == 1


def test_invalid_target_is_rejected(sample_raw):
    sample_raw.loc[0, "num"] = 7
    with pytest.raises(ValueError, match="Target"):
        clean_data(sample_raw)

