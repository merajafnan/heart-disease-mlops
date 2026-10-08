# Windows execution and evidence guide

Use **PowerShell** from the repository root. The lines below assume Python 3.14, matching the version reported on your laptop. If you later choose Python 3.12, change only the first command to `py -3.12 -m venv .venv`. Do not run commands from a parent folder.

## 1. Create the project environment

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks the activation script, run this once in that PowerShell window and retry activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Do not install project dependencies globally. A new PowerShell window requires activation again.

## 2. Prepare data and inspect charts

```powershell
python -m heart_mlops.data
python -m heart_mlops.eda
Get-Content data\processed\data_summary.json
```

Inspect `reports\figures\class_balance.png`, `numeric_histograms.png`, `correlation_heatmap.png`, and `feature_by_target.png`. Capture one screenshot showing the plots and one showing the row counts.

## 3. Test and train

```powershell
ruff check .
python -m pytest -q
python -m heart_mlops.train
Get-Content artifacts\model_metadata.json
```

Record the selected model and actual validation/test metrics from `model_metadata.json`. The test score is only meaningful after the model selection step completes.

## 4. Inspect MLflow

```powershell
mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db --port 5000
```

Open `http://127.0.0.1:5000`. Capture the experiment run list, a candidate's parameters/metrics/artifacts, and the selected model run. Press Ctrl+C in the MLflow PowerShell window when finished.

## 5. Run and test Docker

```powershell
docker build -t heart-disease-api:local .
docker run --name heart-disease-demo --rm -p 8000:8000 heart-disease-api:local
```

In a **second PowerShell window** from the repository root:

```powershell
Invoke-RestMethod http://localhost:8000/health
$payload = Get-Content .\sample_request.json -Raw
Invoke-RestMethod -Uri http://localhost:8000/predict -Method Post -ContentType 'application/json' -Body $payload
Start-Process http://localhost:8000/monitor
Invoke-WebRequest http://localhost:8000/metrics | Select-Object -ExpandProperty Content
docker logs heart-disease-demo
```

Capture the build success, health and prediction responses, monitoring page, and Docker request logs. Stop the first window with Ctrl+C before Kubernetes deployment so port 8000 is free.

## 6. Deploy to Docker Desktop Kubernetes

Ensure Docker Desktop's Kubernetes node is Ready and its context is selected:

```powershell
kubectl config use-context docker-desktop
kubectl get nodes
kubectl apply -f k8s\deployment.yaml
kubectl apply -f k8s\service.yaml
kubectl rollout status deployment/heart-disease-api
kubectl get pods,svc
```

Inspect the `heart-disease-api` LoadBalancer Service. For Docker Desktop local access, try:

```powershell
Invoke-RestMethod http://localhost:8000/health
$payload = Get-Content .\sample_request.json -Raw
Invoke-RestMethod -Uri http://localhost:8000/predict -Method Post -ContentType 'application/json' -Body $payload
kubectl logs deployment/heart-disease-api --tail=20
```

If the LoadBalancer does not respond through localhost, keep the manifest unchanged and diagnose access with `kubectl port-forward service/heart-disease-api 8000:8000` in another terminal. Report whether localhost or port forwarding worked; do not claim a public URL for this local deployment.

Capture `kubectl get pods,svc`, a successful API response, the monitoring page, and the request logs.

## 7. Publish to GitHub

Create an empty GitHub repository named `heart-disease-mlops` in your account. From this project folder:

```powershell
git init -b main
git add .
git commit -m "Build reproducible heart disease MLOps assignment"
git remote add origin https://github.com/YOUR_USERNAME/heart-disease-mlops.git
git push -u origin main
```

Replace `YOUR_USERNAME`. GitHub may prompt you to authenticate in a browser. Do not paste a password or token into chat. Open the Actions tab, wait for the workflow, and capture its green result plus the run artifact. If the workflow fails, inspect the first failed step and send its log excerpt.

## 8. Complete submission evidence

Place your screenshots in `screenshots/` using the names listed there. Rebuild the report with actual Windows metrics, screenshots, and your GitHub URL:

```powershell
python tools\build_report.py --final --repo-url https://github.com/YOUR_USERNAME/heart-disease-mlops
```

Open `reports\Final_Report.docx` and confirm the pages and screenshots look correct. Commit and push the evidence and final report:

```powershell
git add screenshots reports artifacts data
git commit -m "Add Windows run evidence and final report"
git push
```

Record a short screen video using `VIDEO_SCRIPT.md`. Do not substitute screenshots of code for proof that a service ran.
