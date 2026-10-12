# Heart Disease UCI MLOps Assignment

An end-to-end educational ML system for the UCI processed Cleveland dataset. It downloads and cleans the data, creates EDA charts, compares two classifiers with cross validation, tracks experiments in MLflow, serves the selected pipeline with FastAPI, tests it in GitHub Actions, and deploys it to Docker Desktop Kubernetes.

**Scope:** This model is an academic exercise. Its probability is a model score on a small historical dataset and is not a clinical diagnosis or validated personal risk estimate.

## Requirements

- Python 3.12 in Ubuntu 24.04 under WSL 2 was used for the final local run. CI uses Python 3.14; the Dockerfile accepts a Python version build argument so the local image can match WSL.
- Git, Docker Desktop in Linux containers mode with WSL integration, and Docker Desktop Kubernetes with context `docker-desktop`.
- Internet for the initial Python dependency installation and, if restoring the raw file, the UCI download.

See [WSL_RUNBOOK.md](WSL_RUNBOOK.md) for the tested WSL workflow and [WINDOWS_RUNBOOK.md](WINDOWS_RUNBOOK.md) for PowerShell instructions. The report builder in `tools/build_report.py` reads training metadata and the captured Windows screenshots. The completed ten-page report is [reports/Final_Report.docx](reports/Final_Report.docx).

## Quick start

Run from this repository root in Ubuntu/WSL:

```bash
mkdir -p ~/.venvs
python3 -m venv ~/.venvs/heart-disease-mlops
source ~/.venvs/heart-disease-mlops/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m heart_mlops.data
python -m heart_mlops.eda
ruff check .
python -m pytest -q
python -m heart_mlops.train
mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db --port 5000
```

The final command stays running; open `http://127.0.0.1:5000` for the experiment UI in the Windows browser.

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

`docker build` requires `artifacts/model.joblib`, so train first. The default Docker Python is 3.14; pass the WSL Python minor version as a build argument to match the environment that saved the model. Build and run in WSL:

```bash
PYTHON_TAG=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
docker build --build-arg PYTHON_VERSION="$PYTHON_TAG" -t heart-disease-api:local .
docker run --rm -p 8000:8000 heart-disease-api:local
```

In another WSL window, use the sample request as shown in the runbook. Then deploy the same local image from Windows PowerShell to Docker Desktop's Kubernetes cluster:

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

## Deliverables and file locations

1. **Code, Dockerfile, dependencies:** [`heart_mlops/`](heart_mlops/) contains the application code; [`Dockerfile`](Dockerfile) builds the API image; [`requirements.txt`](requirements.txt) and [`requirements-api.txt`](requirements-api.txt) list the development and serving dependencies.
2. **Cleaned data and download instructions:** [`data/processed/heart_disease_clean.csv`](data/processed/heart_disease_clean.csv) and [`data/processed/data_summary.json`](data/processed/data_summary.json) contain the prepared data and counts. [`heart_mlops/data.py`](heart_mlops/data.py) downloads and cleans the UCI source; [`WSL_RUNBOOK.md`](WSL_RUNBOOK.md) gives the command.
3. **EDA, training, inference:** The requested scripts are [`heart_mlops/eda.py`](heart_mlops/eda.py), [`heart_mlops/train.py`](heart_mlops/train.py), [`heart_mlops/predict.py`](heart_mlops/predict.py), and [`heart_mlops/api.py`](heart_mlops/api.py). Plots are in [`reports/figures/`](reports/figures/), and the selected fitted pipeline is [`artifacts/model.joblib`](artifacts/model.joblib).
4. **Unit tests:** [`tests/`](tests/) contains `test_data.py`, `test_model.py`, and `test_api.py`. The conventional plural folder name fulfills the assignment's `test/` requirement.
5. **GitHub Actions workflow:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs linting, tests, data preparation, EDA, training, Docker build, and artifact upload on pushes and pull requests.
6. **Deployment manifests:** [`k8s/deployment.yaml`](k8s/deployment.yaml) and [`k8s/service.yaml`](k8s/service.yaml) deploy the API and local LoadBalancer Service to Docker Desktop Kubernetes.
7. **Screenshot folder:** [`screenshots/`](screenshots/) contains the ten named Windows evidence images and extra MLflow captures. [`screenshots/README.md`](screenshots/README.md) identifies the main images.
8. **Final written report:** [`reports/Final_Report.docx`](reports/Final_Report.docx) is the ten-page report covering EDA, evaluation, MLflow, architecture, CI, Docker, Kubernetes, and monitoring evidence.
9. **Local API access instructions:** This README and [`WINDOWS_RUNBOOK.md`](WINDOWS_RUNBOOK.md) explain `http://localhost:8000/health`, `POST http://localhost:8000/predict` with [`sample_request.json`](sample_request.json), `http://localhost:8000/monitor`, and `/metrics`. The service runs on the Windows laptop's local Docker Desktop cluster; there is no public URL.

The short pipeline video is a separate submission item. [`VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md) lists the scenes and evidence to show.

## Source and limitations

Dataset: Janosi, A. et al., *Heart Disease*, UCI Machine Learning Repository, 1988, https://doi.org/10.24432/C52P4X. The processed Cleveland dataset has 303 records before cleaning. The small, historical data and single train/test split limit performance estimates; no external clinical validation, fairness assessment, or probability calibration is claimed.
