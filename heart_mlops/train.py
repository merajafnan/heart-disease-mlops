"""Compare two classifiers, track experiments, and package the selected model."""

import json
import platform
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import pandas as pd
import sklearn
from mlflow.models import infer_signature
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from heart_mlops.config import (
    ARTIFACT_DIR,
    CATEGORICAL_FEATURES,
    FEATURES,
    FIGURE_DIR,
    MLRUNS_DIR,
    NUMERIC_FEATURES,
    TARGET,
)
from heart_mlops.data import prepare_data

SEED = 42


def make_preprocessor():
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("numeric", numeric, NUMERIC_FEATURES),
        ("categorical", categorical, CATEGORICAL_FEATURES),
    ])


def make_search(model_name: str):
    if model_name == "logistic_regression":
        estimator = LogisticRegression(max_iter=2000, random_state=SEED)
        grid = {"classifier__C": [0.1, 1.0, 10.0],
                "classifier__class_weight": [None, "balanced"]}
    elif model_name == "random_forest":
        estimator = RandomForestClassifier(random_state=SEED, n_jobs=1)
        grid = {"classifier__n_estimators": [100, 200],
                "classifier__max_depth": [None, 5],
                "classifier__min_samples_leaf": [1, 3]}
    else:
        raise ValueError(f"Unknown model: {model_name}")
    pipeline = Pipeline([("preprocess", make_preprocessor()), ("classifier", estimator)])
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    scoring = ["accuracy", "precision", "recall", "roc_auc"]
    return GridSearchCV(
        pipeline, grid, scoring=scoring, refit="roc_auc", cv=cv,
        n_jobs=1, return_train_score=False, error_score="raise",
    )


def _save_cv_plot(search, name: str, folder: Path):
    results = pd.DataFrame(search.cv_results_)
    scores = results["mean_test_roc_auc"]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(range(len(scores)), scores)
    ax.set(xlabel="Grid search candidate", ylabel="Mean 5-fold ROC-AUC",
           title=f"{name.replace('_', ' ').title()} cross validation")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    path = folder / f"{name}_cv_scores.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    results.to_csv(folder / f"{name}_cv_results.csv", index=False)
    return path


def _test_metrics(model, x_test, y_test):
    predictions = model.predict(x_test)
    probability = model.predict_proba(x_test)[:, 1]
    return {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, probability)),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
    }


def train():
    data, data_summary = prepare_data()
    x = data[FEATURES]
    y = data[TARGET]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, stratify=y, random_state=SEED
    )
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    MLRUNS_DIR.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{(MLRUNS_DIR / 'mlflow.db').resolve().as_posix()}")
    mlflow.set_experiment("heart-disease-cleveland")

    candidates = {}
    run_ids = {}
    for name in ("logistic_regression", "random_forest"):
        search = make_search(name)
        with mlflow.start_run(run_name=name) as run:
            mlflow.set_tags({"dataset": "UCI processed Cleveland", "model_family": name})
            mlflow.log_params({"seed": SEED, "train_rows": len(x_train),
                               "test_rows": len(x_test), "cv_folds": 5})
            search.fit(x_train, y_train)
            best_index = search.best_index_
            mlflow.log_params({key.replace("classifier__", ""): str(value)
                               for key, value in search.best_params_.items()})
            cv_metrics = {
                metric: float(search.cv_results_[f"mean_test_{metric}"][best_index])
                for metric in ("accuracy", "precision", "recall", "roc_auc")
            }
            mlflow.log_metrics({f"cv_{key}": value for key, value in cv_metrics.items()})
            plot_path = _save_cv_plot(search, name, FIGURE_DIR)
            mlflow.log_artifact(str(plot_path), artifact_path="plots")
            mlflow.log_artifact(
                str(FIGURE_DIR / f"{name}_cv_results.csv"), artifact_path="tables"
            )
            candidates[name] = {"search": search, "cv_metrics": cv_metrics}
            run_ids[name] = run.info.run_id

    selected_name = max(candidates, key=lambda n: candidates[n]["cv_metrics"]["roc_auc"])
    selected = candidates[selected_name]["search"].best_estimator_
    metrics = _test_metrics(selected, x_test, y_test)
    model_path = ARTIFACT_DIR / "model.joblib"
    joblib.dump(selected, model_path)
    metadata = {
        "selected_model": selected_name,
        "selection_metric": "mean 5-fold ROC-AUC on training split",
        "best_parameters": {key: str(value) for key, value in
                            candidates[selected_name]["search"].best_params_.items()},
        "candidate_cv_metrics": {name: item["cv_metrics"] for name, item in candidates.items()},
        "test_metrics": metrics,
        "data_summary": data_summary,
        "features": FEATURES,
        "seed": SEED,
        "python_version": platform.python_version(),
        "sklearn_version": sklearn.__version__,
        "mlflow_run_ids": run_ids,
    }
    metadata_path = ARTIFACT_DIR / "model_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    ConfusionMatrixDisplay.from_estimator(selected, x_test, y_test, cmap="Blues")
    plt.title("Held out test confusion matrix")
    plt.tight_layout()
    confusion_path = FIGURE_DIR / "test_confusion_matrix.png"
    plt.savefig(confusion_path, dpi=160)
    plt.close()
    RocCurveDisplay.from_estimator(selected, x_test, y_test)
    plt.title("Held out test ROC curve")
    plt.tight_layout()
    roc_path = FIGURE_DIR / "test_roc_curve.png"
    plt.savefig(roc_path, dpi=160)
    plt.close()

    with mlflow.start_run(run_name="selected_model"):
        mlflow.set_tags({"stage": "final_test", "selected_model": selected_name})
        mlflow.log_params({"selection_metric": "cv_roc_auc", "seed": SEED})
        mlflow.log_metrics({f"test_{key}": value for key, value in metrics.items()
                            if key != "confusion_matrix"})
        for path in (model_path, metadata_path):
            mlflow.log_artifact(str(path), artifact_path="model")
        for path in (confusion_path, roc_path):
            mlflow.log_artifact(str(path), artifact_path="plots")
        signature = infer_signature(x_train.head(5), selected.predict(x_train.head(5)))
        mlflow.sklearn.log_model(sk_model=selected, name="selected_pipeline",
                                 signature=signature, input_example=x_train.head(5),
                                 serialization_format="cloudpickle")
    print(json.dumps({"selected_model": selected_name, "test_metrics": metrics}, indent=2))
    return metadata


if __name__ == "__main__":
    train()
