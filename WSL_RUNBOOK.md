# Run the project with WSL and Docker Desktop

This guide uses the project folder on the Windows D drive. WSL shows that drive under `/mnt/d`. Create the Linux virtual environment in your WSL home directory.

## 1. Check the Linux distribution

In **Windows PowerShell**:

```powershell
wsl -l -v
wsl -d Ubuntu
```

Use Ubuntu with WSL version 2. If Ubuntu is absent, run `wsl --install -d Ubuntu`. Restart Windows if requested. Start Ubuntu and create your Linux account. If the distribution has another name, use that name in the command.

Run the next commands in Ubuntu unless a step says PowerShell.

## 2. Enable Docker access inside WSL

In Docker Desktop, open **Settings > Resources > WSL Integration**. Enable Ubuntu and select **Apply & restart**. Then run:

```bash
cat /etc/os-release | head -5
python3 --version
git --version
docker version
docker context ls
```

The output must show the Docker server. Docker Desktop must supply the engine to WSL. If `docker` is absent, check WSL Integration again.

If Ubuntu does not have Python venv support, Git, or curl, install the packages:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git curl
```

Use Python 3.11 or newer with the pinned scikit-learn package. The completed Windows run used Python 3.12.3.

## 3. Enter the existing project folder

```bash
cd /mnt/d/MTECH/Assignment/mlops/heart-disease-mlops-starter/heart-disease-mlops
pwd
ls requirements.txt sample_request.json
```

Use the path of your D-drive checkout. WSL paths use `/`. Match the folder names exactly.

## 4. Create a Linux virtual environment and install packages

```bash
mkdir -p ~/.venvs
python3 -m venv ~/.venvs/heart-disease-mlops
source ~/.venvs/heart-disease-mlops/bin/activate
python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The prompt must show `(heart-disease-mlops)`. In each new WSL terminal, enter the project folder and activate the environment again.

## 5. Prepare data, visualize, test, and train

```bash
python -m heart_mlops.data
python -m heart_mlops.eda
ruff check .
python -m pytest -q
python -m heart_mlops.train
cat artifacts/model_metadata.json
```

Training replaces the included model with one fitted in WSL. Read `model_metadata.json` for the selected model and scores. Find the plots in `reports/figures/`.

## 6. Inspect MLflow

In WSL, run:

```bash
mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db --port 5000
```

Open `http://localhost:5000` in the Windows browser. Save screenshots of candidate runs, parameters, scores, artifacts, and the selected run. Press Ctrl+C to stop MLflow.

## 7. Build and run the Docker API

In WSL:

```bash
PYTHON_TAG=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
docker build --build-arg PYTHON_VERSION="$PYTHON_TAG" -t heart-disease-api:local .
docker run --name heart-disease-demo --rm -p 8000:8000 heart-disease-api:local
```

Keep the first terminal open. In a second WSL terminal, enter the project folder and run:

```bash
cd /mnt/d/MTECH/Assignment/mlops/heart-disease-mlops-starter/heart-disease-mlops
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/predict -H 'Content-Type: application/json' --data @sample_request.json
curl -s http://localhost:8000/stats
docker logs heart-disease-demo --tail 20
```

Open `http://localhost:8000/monitor` in the Windows browser. Save screenshots of the image build, prediction, dashboard, and logs. Press Ctrl+C in the first terminal before Kubernetes uses port 8000.

## 8. Deploy to Kubernetes

The Windows `kubectl` command uses the Docker Desktop context. Open **Windows PowerShell** in the D-drive project folder. Run:

```powershell
cd D:\MTECH\Assignment\mlops\heart-disease-mlops-starter\heart-disease-mlops
kubectl config use-context docker-desktop
kubectl apply -f k8s\deployment.yaml
kubectl apply -f k8s\service.yaml
kubectl rollout status deployment/heart-disease-api
kubectl get pods,svc
Invoke-RestMethod http://localhost:8000/health
$payload = Get-Content .\sample_request.json -Raw
Invoke-RestMethod -Uri http://localhost:8000/predict -Method Post -ContentType 'application/json' -Body $payload
kubectl logs deployment/heart-disease-api --tail=20
```

Save screenshots of the Ready pod, Service, prediction, dashboard, and logs. If localhost does not respond, run `kubectl get svc`. To test port access, run `kubectl port-forward service/heart-disease-api 8000:8000` in another PowerShell window. Then send the request again.

## 9. Review the report and publish changes

The GitHub repository already exists. Open its Actions tab and check the latest workflow run. Save the screenshots listed in `screenshots/README.md`. To rebuild the report, run:

```bash
cd /mnt/d/MTECH/Assignment/mlops/heart-disease-mlops-starter/heart-disease-mlops
source ~/.venvs/heart-disease-mlops/bin/activate
python tools/build_report.py --final --repo-url https://github.com/merajafnan/heart-disease-mlops
```

Open `reports/Final_Report.docx` in Word. Check all ten pages and the screenshots. Close Word before you stage files. In PowerShell, run:

```powershell
git status -sb
git add screenshots reports artifacts data
git commit -m "Add Windows run evidence and final report"
git push origin main
```

Submit the required screen recording separately.
