# Run the project on Windows with WSL

This is the full runbook for a Windows laptop. WSL lets you use Linux Python and Docker commands while the project stays in your chosen Windows folder. Docker Desktop shares its Linux engine with Ubuntu. Use Windows PowerShell for the Docker Desktop Kubernetes cluster and its `kubectl` context.

Open the cloned `heart-disease-mlops` folder in File Explorer. It must contain `requirements.txt` and `sample_request.json`. Use **Open in Terminal** to start PowerShell in that folder. Keep it as your working folder. When you need another terminal, open a new one in the same folder.

Run each command in the shell named above its code block. Do not use a PowerShell command in Ubuntu or a Linux command in PowerShell.

## 1. Check Windows tools and start Ubuntu

Open Docker Desktop. In **Windows PowerShell**, run:

```powershell
Test-Path .\requirements.txt
wsl -l -v
docker version
wsl -d Ubuntu
```

`Test-Path` must return `True`. Ubuntu must use WSL version 2. `docker version` must show both a client and a server. If Ubuntu is absent, run `wsl --install -d Ubuntu` in PowerShell, restart Windows if requested, and create your Ubuntu account. Then open PowerShell in the project folder and run `wsl -d Ubuntu` again.

In **WSL Ubuntu**, check that you are in the project folder:

```bash
pwd
ls requirements.txt sample_request.json
```

If either file is missing, exit Ubuntu, open PowerShell in the folder that contains those files, and start Ubuntu from there.

## 2. Connect Docker Desktop to WSL

In Docker Desktop, open **Settings > Resources > WSL Integration**. Enable Ubuntu and select **Apply & restart**.

In **WSL Ubuntu**, run:

```bash
cat /etc/os-release | head -5
python3 --version
git --version
docker version
docker context ls
```

The Docker output must include a server. If the `docker` command is missing or cannot reach the server, check Docker Desktop and its WSL Integration setting. The completed run used Ubuntu 24.04 and Python 3.12.3. You do not need to upgrade that Python version.

If Ubuntu lacks `venv`, Git, or curl, install them in **WSL Ubuntu**:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git curl
```

## 3. Set up Python and run the project

In **WSL Ubuntu**, create a Linux virtual environment:

```bash
mkdir -p ~/.venvs
python3 -m venv ~/.venvs/heart-disease-mlops
source ~/.venvs/heart-disease-mlops/bin/activate
python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For each new WSL terminal, first open PowerShell in the project folder, run `wsl -d Ubuntu`, and activate the environment with `source ~/.venvs/heart-disease-mlops/bin/activate`. Run the data, EDA, checks, and training commands in **WSL Ubuntu**:

```bash
python -m heart_mlops.data
python -m heart_mlops.eda
ruff check .
python -m pytest -q
python -m heart_mlops.train
cat artifacts/model_metadata.json
```

The data script writes the clean CSV to `data/processed/`. EDA writes plots to `reports/figures/`. The metadata file gives the selected model and test scores.

## 4. Review the MLflow runs

In **WSL Ubuntu**, run:

```bash
mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db --port 5000
```

Open `http://localhost:5000` in a **Windows browser**. Capture the candidate runs, parameters, metrics, artifacts, and selected run. Save the images listed in `screenshots/README.md`. Press Ctrl+C in the WSL terminal when finished.

## 5. Build and test the Docker image

In **WSL Ubuntu**, from the project folder with the virtual environment active, run:

```bash
PYTHON_TAG=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
docker build --build-arg PYTHON_VERSION="$PYTHON_TAG" -t heart-disease-api:local .
docker run --name heart-disease-demo --rm -p 8000:8000 heart-disease-api:local
```

Leave this terminal open. Open another PowerShell terminal in the project folder and run `wsl -d Ubuntu`. In that **second WSL Ubuntu terminal**, run:

```bash
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/predict -H 'Content-Type: application/json' --data @sample_request.json
curl -s http://localhost:8000/stats
curl -s http://localhost:8000/metrics
docker logs heart-disease-demo --tail 20
```

Open `http://localhost:8000/monitor` in a **Windows browser**. Capture the image build, prediction, dashboard, and request logs. Press Ctrl+C in the first WSL terminal before the Kubernetes step. Port 8000 must be free for the Kubernetes Service.

## 6. Deploy to Docker Desktop Kubernetes

In Docker Desktop, enable Kubernetes and wait for it to start. Open **Windows PowerShell** in the project folder and run:

```powershell
Test-Path .\requirements.txt
kubectl config use-context docker-desktop
kubectl get nodes
docker image inspect heart-disease-api:local --format '{{.Id}}'
kubectl apply -f k8s\deployment.yaml
kubectl apply -f k8s\service.yaml
kubectl rollout status deployment/heart-disease-api
kubectl get pods,svc
```

`Test-Path` must return `True`. The node must show `Ready`. The image check must return an image ID. The pod must show `Running` and `1/1` Ready. The Service must show `LoadBalancer` and port 8000.

Test the API in **Windows PowerShell**:

```powershell
Invoke-RestMethod http://localhost:8000/health
$payload = Get-Content .\sample_request.json -Raw
Invoke-RestMethod -Uri http://localhost:8000/predict -Method Post -ContentType 'application/json' -Body $payload
Invoke-WebRequest http://localhost:8000/metrics | Select-Object -ExpandProperty Content
kubectl logs deployment/heart-disease-api --tail=20
```

Open `http://localhost:8000/monitor` in a **Windows browser**. Capture the Ready pod, Service, prediction, dashboard, and logs. If the API does not answer, check `kubectl get svc heart-disease-api`. You can run `kubectl port-forward service/heart-disease-api 8000:8000` in a second PowerShell window and send the request again. The API has no public URL.

## 7. Check the evidence and final report

In a **Windows browser**, open the repository's GitHub **Actions** tab. Check the latest `Heart disease ML CI` run and its artifact. Save the screenshots named in `screenshots/README.md`.

To rebuild the report, open PowerShell in the project folder and run `wsl -d Ubuntu`. Then run these commands in **WSL Ubuntu**:

```bash
source ~/.venvs/heart-disease-mlops/bin/activate
python tools/build_report.py --final --repo-url https://github.com/merajafnan/heart-disease-mlops
```

Open `reports/Final_Report.docx` in **Windows Word**. Check its ten pages and images. Close Word before staging files. Open **Windows PowerShell** in the project folder and run:

```powershell
git status -sb
git add screenshots reports artifacts data
git commit -m "Add Windows run evidence and final report"
git push origin main
```

Run the commit command only if `git status` shows changes to submit. Submit the required screen recording separately.
