# Heart Disease UCI MLOps Assignment

An end-to-end educational ML system for the UCI processed Cleveland dataset. It downloads and cleans the data, creates EDA charts, compares two classifiers with cross validation, tracks experiments in MLflow, serves the selected pipeline with FastAPI, tests it in GitHub Actions, and deploys it to Docker Desktop Kubernetes.

**Scope:** This model is an academic exercise. Its probability is a model score on a small historical dataset and is not a clinical diagnosis or validated personal risk estimate.

## Requirements

- Python 3.14 (the provided Windows environment); Python 3.12 may also work, but the supplied CI and Docker image use 3.14.
- Git for Windows, Docker Desktop in Linux containers mode, and Docker Desktop Kubernetes with context `docker-desktop`.
- Internet for the initial Python dependency installation and, if restoring the raw file, the UCI download.

See [WINDOWS_RUNBOOK.md](WINDOWS_RUNBOOK.md) for copy-and-paste PowerShell instructions.
If you prefer Linux commands through Windows Subsystem for Linux, use [WSL_RUNBOOK.md](WSL_RUNBOOK.md). It uses Docker Desktop's WSL integration and the same D-drive project folder.
The report builder in `tools/build_report.py` reads actual training metadata and inserts the Windows screenshots once they exist. `reports/Report_Draft.docx` is the current 10-page draft; use the runbook to produce `reports/Final_Report.docx` after the Windows evidence is captured.

## Quick start

Run from this repository root. In PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m heart_mlops.data
python -m heart_mlops.eda
ruff check .
python -m pytest -q
python -m heart_mlops.train
mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db --port 5000
```

The final command stays running; open `http://127.0.0.1:5000` for the experiment UI. If your installed interpreter is 3.12, replace `py -3.14` with `py -3.12` when creating the virtual environment.

## Data and modeling

The raw file is `data/raw/processed.cleveland.data`, downloaded from [UCI](https://archive.ics.uci.edu/dataset/45/heart+disease). Its SHA-256 digest is checked before saving. The data preparation script parses the 13 features and original target, drops incomplete or duplicate rows, and converts targets 1–4 to class 1 and target 0 to class 0. The output is `data/processed/heart_disease_clean.csv`; `data_summary.json` records row counts and provenance.

The cleaned dataset is split 80/20 with stratification and seed 42. For each candidate, preprocessing is fitted only inside its cross validation training folds: numeric median imputation and scaling; categorical mode imputation and one hot encoding. Logistic Regression and Random Forest receive grid searches with five stratified folds. Mean validation ROC-AUC selects the final model. The held out test set is used once after selection; its accuracy, precision, recall, ROC-AUC, confusion matrix, and ROC curve are recorded. The fitted preprocessing and classifier are saved together in `artifacts/model.joblib`. The scikit-learn version is pinned across training and the smaller API image requirements to keep model loading compatible.

Model probabilities and `confidence` come from `predict_proba`. They are not calibrated clinical risk probabilities. The classification threshold is 0.5.

## API

After training, start the API locally:

```powershell
uvicorn heart_mlops.api:app --host 127.0.0.1 --port 8000
```

Endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Readiness check; fails if the model is absent |
| `POST /predict` | Accepts all 13 UCI feature values as JSON |
| `GET /docs` | Interactive OpenAPI documentation |
| `GET /metrics` | Prometheus format request counts and duration |
| `GET /monitor` | Small live request dashboard |
| `GET /stats` | JSON counters used by the dashboard |

Use `sample_request.json` for a valid sample. The response gives a binary prediction, label, positive class probability, and confidence. The service logs request method, path, status, and duration without logging patient values.

## Docker and Kubernetes

`docker build` requires `artifacts/model.joblib`, so train first. The default Docker Python is 3.14; the WSL guide passes its active Python minor version as a build argument to match the environment that saved the model. Build and run from Windows PowerShell:

```powershell
docker build -t heart-disease-api:local .
docker run --rm -p 8000:8000 heart-disease-api:local
```

In another PowerShell window, use `Invoke-RestMethod` as shown in the runbook. Then deploy the same local image to Docker Desktop's `kubeadm` Kubernetes cluster:

```powershell
kubectl config use-context docker-desktop
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl rollout status deployment/heart-disease-api
kubectl get pods,svc
```

The Service is type `LoadBalancer`. Docker Desktop normally makes the service available through localhost; inspect `kubectl get svc heart-disease-api` for the actual address. `kubectl port-forward service/heart-disease-api 8000:8000` is documented as an access diagnostic if local load balancer networking differs.

## CI and artifacts

`.github/workflows/ci.yml` runs on pushes and pull requests. It installs dependencies, lints, runs unit tests, prepares data, creates EDA figures, trains and tracks both models, builds the Docker image, and uploads generated evidence as a workflow artifact. A lint, test, training, or build error fails the workflow.

The selected model in `artifacts/` is included in the repository after training. `mlruns/` is excluded from Git because CI uploads the experiment store as a workflow artifact. The cleaned dataset, EDA figures, and report also live in the repository. CI builds its Docker image from a freshly trained model.

## Repository contents

| Path | Contents |
|---|---|
| `heart_mlops/data.py` | UCI acquisition, parsing, cleaning, target mapping |
| `heart_mlops/eda.py` | Four EDA plots |
| `heart_mlops/train.py` | Pipelines, cross validation, MLflow, evaluation |
| `heart_mlops/predict.py` | Reusable model inference |
| `heart_mlops/api.py` | FastAPI and monitoring |
| `tests/` | Data, model, and API tests |
| `k8s/` | Deployment and LoadBalancer Service |
| `reports/` | EDA/evaluation figures and report |
| `screenshots/` | Evidence captured on the Windows laptop |

## Source and limitations

Dataset: Janosi, A. et al., *Heart Disease*, UCI Machine Learning Repository, 1988, https://doi.org/10.24432/C52P4X. The processed Cleveland dataset has 303 records before cleaning. The small, historical data and single train/test split limit performance estimates; no external clinical validation, fairness assessment, or probability calibration is claimed.
