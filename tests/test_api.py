import numpy as np
import pytest
from fastapi.testclient import TestClient

from heart_mlops.api import app


class FakeModel:
    def predict_proba(self, frame):
        assert frame.shape == (1, 13)
        return np.array([[0.2, 0.8]])


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("heart_mlops.predict.load_model", lambda: FakeModel())
    monkeypatch.setattr("heart_mlops.api.load_model", lambda: FakeModel())
    return TestClient(app)


def test_prediction_and_health(client):
    payload = {
        "age": 54, "sex": 1, "cp": 4, "trestbps": 130, "chol": 239,
        "fbs": 0, "restecg": 2, "thalach": 126, "exang": 1,
        "oldpeak": 2.8, "slope": 2, "ca": 1, "thal": 7,
    }
    assert client.get("/health").json() == {"status": "ready"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json()["prediction"] == 1
    assert response.json()["confidence"] == 0.8
    assert client.get("/metrics").status_code == 200
    assert client.get("/stats").json()["prediction_requests"] >= 1


def test_invalid_feature_is_rejected(client):
    assert client.post("/predict", json={"age": 54}).status_code == 422
