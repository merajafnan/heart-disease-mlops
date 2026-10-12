# Heart disease MLOps assignment

This project uses the UCI processed Cleveland heart disease data. It cleans the data and compares two models. MLflow records the runs. FastAPI serves the selected model. Docker Desktop Kubernetes runs the API.

This is an academic model. Its probability is a model score, not a clinical diagnosis or a validated risk estimate.

## Requirements

- The Windows run used Python 3.12.3 in Ubuntu 24.04 under WSL 2. GitHub Actions uses Python 3.14.
- Use Git and Docker Desktop with Linux containers and WSL integration. Enable the `docker-desktop` Kubernetes context.
- You need internet access to install packages. You also need it if you download the UCI source file again.

Use [RUNBOOK.md](RUNBOOK.md) for the complete Windows and WSL procedure. The report is [reports/Final_Report.docx](reports/Final_Report.docx).

## Quick start

Open Ubuntu under WSL. Run these commands from the repository root:

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

Keep the last command active. Open `http://127.0.0.1:5000` in the Windows browser to see the MLflow runs.

## Data and modeling

The raw file is `data/raw/processed.cleveland.data` from [UCI](https://archive.ics.uci.edu/dataset/45/heart+disease). The download script checks its SHA-256 digest. It reads 13 inputs and the original target. It removes incomplete and duplicate rows. It maps targets 1 through 4 to class 1 and target 0 to class 0. The clean file is `data/processed/heart_disease_clean.csv`. `data_summary.json` gives the row counts and source.

The script splits the clean data into 80% training rows and 20% test rows. It uses stratification and seed 42. The pipeline learns preprocessing values within each training fold. Numeric inputs use median imputation and scaling. Categorical inputs use mode imputation and one-hot encoding.

Grid search tests Logistic Regression and Random Forest with five stratified folds. Mean validation ROC-AUC selects the model. The script tests that model once on the held-out rows. It records accuracy, precision, recall, ROC-AUC, a confusion matrix, and an ROC curve. `artifacts/model.joblib` contains the fitted preprocessing and classifier. The training and API requirements pin the same scikit-learn version.

`predict_proba` supplies the model probability and `confidence`. These values are not calibrated clinical risks. The class threshold is 0.5.

## API

After training, start the local API:

```bash
uvicorn heart_mlops.api:app --host 127.0.0.1 --port 8000
```

Endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Check that the model is ready |
| `POST /predict` | Accepts all 13 UCI feature values as JSON |
| `GET /docs` | Interactive OpenAPI documentation |
| `GET /metrics` | Show request counts and duration in Prometheus format |
| `GET /monitor` | Show the request dashboard |
| `GET /stats` | Give JSON counters to the dashboard |

Send `sample_request.json` to `/predict`. The response has the class, label, positive-class probability, and confidence. Request logs contain method, path, status, and duration. They do not contain patient values.

## Docker and Kubernetes

Train the model before you build the image. The build needs `artifacts/model.joblib`. Use the WSL Python version for the image. Run these commands in WSL:

```bash
PYTHON_TAG=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
docker build --build-arg PYTHON_VERSION="$PYTHON_TAG" -t heart-disease-api:local .
docker run --rm -p 8000:8000 heart-disease-api:local
```

Test the container from another WSL window. The runbook gives the request. Then open Windows PowerShell and deploy the image:

```powershell
kubectl config use-context docker-desktop
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl rollout status deployment/heart-disease-api
kubectl get pods,svc
```

The Service type is `LoadBalancer`. Check its address with `kubectl get svc heart-disease-api`. On Docker Desktop, the API normally uses `localhost:8000`. If it does not respond, use `kubectl port-forward service/heart-disease-api 8000:8000` to test access.

## CI and artifacts

`.github/workflows/ci.yml` runs after each push and pull request. It installs packages, runs Ruff and Pytest, prepares data, creates plots, trains models, and builds the image. It uploads the run files as an artifact. A required step that fails makes the job fail.

The repository includes the selected model, clean data, plots, and report. Git excludes `mlruns/`. The workflow uploads that store as an artifact. It builds the image from the model trained in the same job.

## Deliverables and file locations

1. **Code, Dockerfile, dependencies:** [`heart_mlops/`](heart_mlops/) has the code. [`Dockerfile`](Dockerfile) builds the API image. [`requirements.txt`](requirements.txt) and [`requirements-api.txt`](requirements-api.txt) list the packages.
2. **Cleaned data and download instructions:** [`data/processed/heart_disease_clean.csv`](data/processed/heart_disease_clean.csv) has the clean data. [`data/processed/data_summary.json`](data/processed/data_summary.json) has the counts. [`heart_mlops/data.py`](heart_mlops/data.py) downloads and cleans the source. [`RUNBOOK.md`](RUNBOOK.md) gives the command.
3. **EDA, training, inference:** [`heart_mlops/eda.py`](heart_mlops/eda.py), [`heart_mlops/train.py`](heart_mlops/train.py), [`heart_mlops/predict.py`](heart_mlops/predict.py), and [`heart_mlops/api.py`](heart_mlops/api.py) are the scripts. [`reports/figures/`](reports/figures/) has plots. [`artifacts/model.joblib`](artifacts/model.joblib) has the fitted model.
4. **Unit tests:** [`tests/`](tests/) has `test_data.py`, `test_model.py`, and `test_api.py`.
5. **GitHub Actions workflow:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs tests, model training, and the Docker build. It also uploads the run files.
6. **Deployment manifests:** [`k8s/deployment.yaml`](k8s/deployment.yaml) starts the API pod. [`k8s/service.yaml`](k8s/service.yaml) exposes port 8000 on the local cluster.
7. **Screenshot folder:** [`screenshots/`](screenshots/) has ten main Windows screenshots and extra MLflow views. [`screenshots/README.md`](screenshots/README.md) lists the main images.
8. **Final written report:** [`reports/Final_Report.docx`](reports/Final_Report.docx) is the ten-page report. It includes results, figures, and run screenshots.
9. **Local API access instructions:** This README and [`RUNBOOK.md`](RUNBOOK.md) give the localhost URLs and request commands. The API has no public URL.

## Source and limitations

Dataset: Janosi, A. et al., *Heart Disease*, UCI Machine Learning Repository, 1988, https://doi.org/10.24432/C52P4X.

The processed Cleveland file has 303 rows before cleaning. The dataset is small and historical. This work has no external clinical validation or fairness assessment. Model probabilities are not calibrated clinical risks.
