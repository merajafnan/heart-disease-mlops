# Windows PowerShell checks

Use [WSL_RUNBOOK.md](WSL_RUNBOOK.md) to prepare data, train the model, and build the Docker image in Ubuntu. Use this guide for Windows PowerShell checks. Run the commands from the D-drive project folder.

## 1. Check Docker Desktop and Kubernetes

Open Docker Desktop. Start its Kubernetes cluster. Then open Windows PowerShell and run:

```powershell
cd D:\MTECH\Assignment\mlops\heart-disease-mlops-starter\heart-disease-mlops
docker version
kubectl config use-context docker-desktop
kubectl get nodes
docker image inspect heart-disease-api:local --format '{{.Id}}'
```

The node status must be `Ready`. The image check must return an image ID. If the image is absent, build it with the WSL runbook.

## 2. Test the local container

Make sure port 8000 is free. If Kubernetes uses that port, skip to section 3. To test the container, run:

```powershell
docker run --name heart-disease-demo --rm -p 8000:8000 heart-disease-api:local
```

Keep that window open. Open a second PowerShell window in the same folder. Run:

```powershell
Invoke-RestMethod http://localhost:8000/health
$payload = Get-Content .\sample_request.json -Raw
Invoke-RestMethod -Uri http://localhost:8000/predict -Method Post -ContentType 'application/json' -Body $payload
Start-Process http://localhost:8000/monitor
Invoke-WebRequest http://localhost:8000/metrics | Select-Object -ExpandProperty Content
docker logs heart-disease-demo
```

Save screenshots of the health result, prediction, dashboard, and request logs. Press Ctrl+C in the first window before the Kubernetes test.

## 3. Deploy to Kubernetes

Run these commands from the project folder:

```powershell
kubectl apply -f k8s\deployment.yaml
kubectl apply -f k8s\service.yaml
kubectl rollout status deployment/heart-disease-api
kubectl get pods,svc
```

The pod must show `Running` and `1/1` Ready. The Service type must be `LoadBalancer`. Test the local API:

```powershell
Invoke-RestMethod http://localhost:8000/health
$payload = Get-Content .\sample_request.json -Raw
Invoke-RestMethod -Uri http://localhost:8000/predict -Method Post -ContentType 'application/json' -Body $payload
kubectl logs deployment/heart-disease-api --tail=20
```

Open `http://localhost:8000/monitor` in the Windows browser. Save the pod, Service, prediction, dashboard, and log results.

If localhost does not respond, run `kubectl get svc heart-disease-api` to check the Service. Use `kubectl port-forward service/heart-disease-api 8000:8000` in another window to test access. The API has no public URL.

## 4. Check the submission files

Use [screenshots/README.md](screenshots/README.md) to check the ten main screenshots. Open [reports/Final_Report.docx](reports/Final_Report.docx) in Word. Check its ten pages and figures. The GitHub Actions workflow is [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Check its latest run on GitHub after you push changes.

Submit the required screen recording separately.
