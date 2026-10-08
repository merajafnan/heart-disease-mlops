import pandas as pd
import pytest

from heart_mlops.config import RAW_COLUMNS


@pytest.fixture
def sample_raw():
    return pd.DataFrame([
        [63, 1, 1, 145, 233, 1, 2, 150, 0, 2.3, 3, 0, 6, 0],
        [67, 1, 4, 160, 286, 0, 2, 108, 1, 1.5, 2, 3, 3, 2],
        [54, 0, 3, 120, 220, 0, 0, 160, 0, 0, 1, "?", 3, 1],
    ], columns=RAW_COLUMNS)

