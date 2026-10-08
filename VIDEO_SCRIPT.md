# Short pipeline demonstration video

Record your Windows screen after completing the runbook. Aim for roughly four minutes and speak in your own words. Use real output from your run.

1. **Project and dataset, 30 seconds.** Show the GitHub repository, source link, cleaned data summary, and EDA charts.
2. **Training and MLflow, 60 seconds.** Show both model runs, cross validation ROC-AUC, selected model, held out test metrics, and logged plots/artifacts.
3. **Tests and CI, 40 seconds.** Show local Pytest output and the successful GitHub Actions run with its artifact.
4. **Docker API, 50 seconds.** Show the built image, `/health`, a sample `/predict` JSON request, and its response.
5. **Kubernetes and monitoring, 60 seconds.** Show a Ready pod, LoadBalancer Service, deployed prediction, `/monitor` or `/metrics`, and structured request logs.

End by stating that this is an educational model based on a small historical dataset and is not for clinical decision making. Save the recording in a format your course accepts and place it with the submission; large video files should not be committed to Git unless the course specifically asks for that.

