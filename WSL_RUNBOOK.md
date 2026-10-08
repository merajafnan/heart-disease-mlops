# Run the assignment with WSL and Docker Desktop

This guide uses your existing project folder on the Windows D drive. WSL sees it under `/mnt/d`. The data is small, so this avoids moving files between Windows and Linux. The old Windows `.venv` folder is left alone; a separate Linux virtual environment is created in your WSL home directory.

## 1. Check the Linux distribution

In **Windows PowerShell**:

```powershell
wsl -l -v
wsl -d Ubuntu
```

You need a user distribution such as Ubuntu with `VERSION 2`. If Ubuntu is not listed, install it with `wsl --install -d Ubuntu`, restart Windows if prompted, and launch Ubuntu once to create your Linux username. If your user distribution has a different name, substitute that name for `Ubuntu` in the launch command.

All commands below are in the **WSL Linux terminal** unless marked PowerShell.

## 2. Enable Docker access inside WSL

In Docker Desktop on Windows, open **Settings > Resources > WSL Integration**, enable your Ubuntu distribution, and select **Apply & restart**. Return to WSL and check:

```bash
cat /etc/os-release | head -5
python3 --version
git --version
docker version
docker context ls
```

The Docker server must appear and the current context should use Docker Desktop. Do not install a second Docker Engine inside WSL. If `docker` is unavailable, recheck the Docker Desktop WSL Integration setting.

For Ubuntu, if Python virtual environment support, Git, or curl is missing, install it with:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git curl
```

The WSL Python interpreter should be **3.11 or newer** for the pinned scikit-learn release. If it is older, stop and report the distribution and Python version so the appropriate Linux Python can be installed.

## 3. Enter the existing project folder

```bash
cd /mnt/d/MTECH/Assignment/mlops/heart-disease-mlops-starter/heart-disease-mlops
pwd
ls requirements.txt sample_request.json
```

The path uses the D-drive folder shown in your PowerShell output. Linux paths use `/`, and letter case may matter inside WSL.

## 4. Create a Linux virtual environment and install packages

```bash
mkdir -p ~/.venvs
python3 -m venv ~/.venvs/heart-disease-mlops
source ~/.venvs/heart-disease-mlops/bin/activate
python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The prompt should show `(heart-disease-mlops)`. In a new WSL terminal, return to the project directory and run `source ~/.venvs/heart-disease-mlops/bin/activate` again. Do not use the Windows `.venv` under the project directory.

## 5. Prepare data, visualize, test, and train

```bash
python -m heart_mlops.data
python -m heart_mlops.eda
ruff check .
python -m pytest -q
python -m heart_mlops.train
cat artifacts/model_metadata.json
```

The training command overwrites the included development model with a model fitted in your WSL environment. Record the actual selected model and metrics. EDA and evaluation figures are in `reports/figures/`.

## 6. Inspect MLflow

In WSL, run:

```bash
mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db --port 5000
```

Open `http://localhost:5000` in the Windows browser. Capture the candidate runs, parameters, metrics, artifacts, and selected model run. Press Ctrl+C in WSL when finished.

## 7. Build and run the Docker API

In WSL:

```bash
PYTHON_TAG=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
docker build --build-arg PYTHON_VERSION="$PYTHON_TAG" -t heart-disease-api:local .
docker run --name heart-disease-demo --rm -p 8000:8000 heart-disease-api:local
```

Keep that terminal running. Open a **second WSL terminal**, enter the project folder, and test:

```bash
cd /mnt/d/MTECH/Assignment/mlops/heart-disease-mlops-starter/heart-disease-mlops
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/predict -H 'Content-Type: application/json' --data @sample_request.json
curl -s http://localhost:8000/stats
docker logs heart-disease-demo --tail 20
```

Open `http://localhost:8000/monitor` in the Windows browser. Capture the build, prediction, monitoring page, and logs. Stop the first terminal with Ctrl+C to free port 8000.

## 8. Deploy to Kubernetes

The Windows `kubectl` is already configured and your Docker Desktop node is Ready. Use **Windows PowerShell** from the same D-drive project folder, so no extra Kubernetes installation or kubeconfig copy is needed:

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

Capture the Ready pod, LoadBalancer Service, prediction, monitor, and logs. If localhost access does not work, check the service address in `kubectl get svc`. As a diagnostic, run `kubectl port-forward service/heart-disease-api 8000:8000` in a separate PowerShell window and retry the request.

## 9. Publish and complete submission

Create an empty GitHub repository named `heart-disease-mlops` in your browser. In **Windows PowerShell**, from the D-drive project folder:

```powershell
git init -b main
git add .
git commit -m "Build reproducible heart disease MLOps assignment"
git remote add origin https://github.com/YOUR_USERNAME/heart-disease-mlops.git
git push -u origin main
```

Replace `YOUR_USERNAME`. If Git asks for your name/email, configure them locally before retrying the commit; do not share account credentials in chat. Open GitHub Actions, wait for the workflow, and capture the result and workflow artifact. Save the ten screenshots listed in `screenshots/README.md` into the D-drive project folder. Back in WSL, activate the environment and generate the final report:

```bash
cd /mnt/d/MTECH/Assignment/mlops/heart-disease-mlops-starter/heart-disease-mlops
source ~/.venvs/heart-disease-mlops/bin/activate
python tools/build_report.py --final --repo-url https://github.com/YOUR_USERNAME/heart-disease-mlops
```

Open `reports/Final_Report.docx` in Word on Windows and review the pages. In PowerShell, commit and push the final screenshots/report:

```powershell
git add screenshots reports artifacts data
git commit -m "Add Windows run evidence and final report"
git push
```

Record the short demonstration video using `VIDEO_SCRIPT.md` and submit it according to your course instructions.
