from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "processed.cleveland.data"
CLEAN_PATH = ROOT / "data" / "processed" / "heart_disease_clean.csv"
ARTIFACT_DIR = ROOT / "artifacts"
FIGURE_DIR = ROOT / "reports" / "figures"
MLRUNS_DIR = ROOT / "mlruns"

FEATURES = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal",
]
NUMERIC_FEATURES = ["age", "trestbps", "chol", "thalach", "oldpeak"]
CATEGORICAL_FEATURES = [
    "sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal",
]
TARGET = "heart_disease"
RAW_COLUMNS = [*FEATURES, "num"]
SOURCE_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/"
    "heart-disease/processed.cleveland.data"
)
RAW_SHA256 = "a74b7efa387bc9d108d7d0115d831fe9b414b29ae7124f331b622b4efa0427c8"

