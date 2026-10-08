import numpy as np
import pandas as pd

from heart_mlops.config import FEATURES
from heart_mlops.predict import predict_one
from heart_mlops.train import make_search


def test_pipeline_trains_and_predicts_with_original_feature_names():
    base = [54, 1, 4, 130, 239, 0, 2, 126, 1, 2.8, 2, 1, 7]
    rows = []
    labels = []
    for index in range(30):
        row = base.copy()
        row[0] = 40 + index
        row[7] = 170 - index
        row[11] = index % 4
        rows.append(row)
        labels.append(index % 2)
    x = pd.DataFrame(rows, columns=FEATURES)
    search = make_search("logistic_regression")
    search.fit(x, np.array(labels))
    result = predict_one(dict(x.iloc[0]), model=search.best_estimator_)
    assert result["prediction"] in (0, 1)
    assert 0 <= result["heart_disease_probability"] <= 1

