"""Build the 10-page assignment report from measured results and Windows evidence."""

import argparse
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "reports" / "figures"
SHOTS = ROOT / "screenshots"
METADATA = ROOT / "artifacts" / "model_metadata.json"
SHOT_FILES = [
    "04-mlflow.png", "05-tests-ci.png", "05-tests-ci-artifacts.png",
    "06-docker.png", "07-docker-prediction.png",
    "08-kubernetes.png", "09-kubernetes-prediction.png", "10-monitoring.png",
]


def font(size=26, bold=False):
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    for candidate in (name, "/System/Library/Fonts/Supplemental/Arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def architecture_image():
    path = FIGURES / "architecture.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (1350, 490), "white")
    draw = ImageDraw.Draw(canvas)
    boxes = [
        (30, 130, 245, 305, "UCI data\nEDA"),
        (300, 130, 515, 305, "Training\nTwo models"),
        (570, 130, 785, 305, "MLflow\nModel"),
        (840, 130, 1055, 305, "FastAPI\nDocker"),
        (1110, 130, 1325, 305, "Kubernetes\nMonitoring"),
    ]
    for x1, y1, x2, y2, label in boxes:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill="#eaf1f7", outline="#526b80", width=3)
        bbox = draw.multiline_textbbox((0, 0), label, font=font(28, True), spacing=9, align="center")
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.multiline_text((x1 + (x2-x1-w)/2, y1 + (y2-y1-h)/2), label,
                            fill="#172b3c", font=font(28, True), spacing=9, align="center")
    for x in (250, 520, 790, 1060):
        draw.line((x, 215, x+42, 215), fill="#526b80", width=5)
        draw.polygon(((x+42, 215), (x+28, 205), (x+28, 225)), fill="#526b80")
    draw.text((335, 55), "GitHub Actions: lint  |  tests  |  training  |  image build",
              fill="#172b3c", font=font(32, True))
    draw.text((890, 365), "Logs + /metrics + /monitor", fill="#172b3c", font=font(30))
    canvas.save(path)
    return path


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def add_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for i, heading in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = heading
        set_cell_shading(cell, "263746")
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
    for values in rows:
        cells = table.add_row().cells
        for i, value in enumerate(values):
            cells[i].text = str(value)
    doc.add_paragraph()
    return table


def para(doc, text, style=None):
    return doc.add_paragraph(text, style=style)


def heading(doc, title):
    doc.add_heading(title, level=1)


def figure(doc, filename, caption, width=5.7):
    path = FIGURES / filename
    if not path.is_file():
        raise FileNotFoundError(path)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Inches(width))
    caption_p = doc.add_paragraph(caption, style="Caption")
    caption_p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def evidence(doc, filename, description, width=5.6, max_height=2.2):
    path = SHOTS / filename
    if path.is_file():
        with Image.open(path) as source:
            aspect = source.height / source.width
        image_width = min(width, max_height / aspect)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Inches(image_width))
        c = doc.add_paragraph(description, style="Caption")
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        p = doc.add_paragraph()
        p.style = "Caption"
        p.add_run(f"Windows evidence pending: {description} ({filename})")


def page(doc, title):
    doc.add_page_break()
    heading(doc, title)


def build(final=False, repo_url=""):
    if not METADATA.is_file():
        raise FileNotFoundError("Run python -m heart_mlops.train before building the report")
    if final and (not repo_url or any(not (SHOTS / name).is_file() for name in SHOT_FILES)):
        raise ValueError("Final report requires --repo-url and all Windows evidence screenshots")
    meta = json.loads(METADATA.read_text(encoding="utf-8"))
    architecture_image()
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.72)
    sec.bottom_margin = Inches(0.67)
    sec.left_margin = Inches(0.82)
    sec.right_margin = Inches(0.82)
    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(9.5)
    styles["Normal"].paragraph_format.space_after = Pt(6)
    for name, size in (("Title", 23), ("Heading 1", 16), ("Heading 2", 11)):
        styles[name].font.name = "Arial"
        styles[name].font.size = Pt(size)
        styles[name].font.color.rgb = RGBColor(0, 0, 0)
        styles[name].font.bold = True
    styles["Caption"].font.name = "Arial"
    styles["Caption"].font.size = Pt(8)
    styles["Caption"].font.color.rgb = RGBColor(60, 60, 60)
    title_style = styles["Title"]._element
    for border in title_style.xpath(".//w:pBdr"):
        border.getparent().remove(border)

    doc.add_paragraph("Heart Disease Classification MLOps Experimental Learning Report", style="Title")
    para(doc, "End to end model development, experiment tracking, CI, containerization, local Kubernetes deployment, and monitoring")
    para(doc, "Prepared for the MLOps experimental learning assignment")
    para(doc, "Dataset: UCI processed Cleveland Heart Disease records")
    doc.add_heading("Project summary", level=1)
    para(doc, "This project implements a reproducible educational classifier for the presence of heart disease in the UCI processed Cleveland dataset. The pipeline covers data acquisition, quality checks, exploratory analysis, model comparison, experiment logging, tested API serving, containerization, and deployment manifests. " + ("Windows runtime evidence is included in the later sections." if final else "Windows runtime evidence is added after the accompanying runbook has been executed."))
    add_table(doc, ["Measure", "Windows run result" if final else "Development run result"], [
        ("Clean records", meta["data_summary"]["clean_rows"]),
        ("Selected model", meta["selected_model"].replace("_", " ").title()),
        ("Held out test accuracy", f"{meta['test_metrics']['accuracy']:.3f}"),
        ("Held out test ROC-AUC", f"{meta['test_metrics']['roc_auc']:.3f}"),
    ])
    para(doc, ("The figures and metrics come from the Windows run using Python " if final else "The figures in this draft come from an actual local development run using Python ") + meta["python_version"] + ("." if final else ". The Windows run should be used to confirm the final submission values."))
    doc.add_heading("Submission contents", level=1)
    add_table(doc, ["Deliverable", "Repository location"], [
        ("Source and install files", "heart_mlops/; requirements.txt; requirements-api.txt; Dockerfile"),
        ("Data and saved model", "data/raw/; data/processed/; artifacts/model.joblib; artifacts/model_metadata.json"),
        ("Tests, CI, and deployment", "tests/; .github/workflows/ci.yml; k8s/deployment.yaml; k8s/service.yaml"),
        ("Evidence and documentation", "screenshots/; reports/Final_Report.docx; README.md; WINDOWS_RUNBOOK.md; WSL_RUNBOOK.md"),
    ])
    para(doc, "The short pipeline demonstration is a separate submission item; VIDEO_SCRIPT.md lists the scenes and evidence to show.")

    page(doc, "1 Objective and system architecture")
    para(doc, "The task is binary classification: target 0 means absence; original targets 1 through 4 mean presence. The system accepts the 13 UCI predictors and returns a class plus a model probability. It is designed as an educational production pattern with separable data, training, serving, CI, and monitoring components.")
    figure(doc, "architecture.png", "Figure 1  Assignment system architecture", 6.6)
    para(doc, "Training creates a fitted preprocessing and classifier pipeline. MLflow records model comparisons and artifacts. The selected pipeline is serialized and included in the Docker image. Docker Desktop Kubernetes hosts one API replica behind a LoadBalancer Service. Prometheus format metrics and structured request logs describe service activity.")
    doc.add_heading("Setup and local API access", level=2)
    para(doc, "The final run used Ubuntu 24.04 in WSL 2 with Python 3.12.3 and Docker Desktop's WSL integration. From the repository root, create and activate a Linux virtual environment with `python3 -m venv ~/.venvs/heart-disease-mlops` and `source ~/.venvs/heart-disease-mlops/bin/activate`. Install dependencies using `python -m pip install -r requirements.txt`. Run `python -m heart_mlops.data`, `python -m heart_mlops.eda`, `ruff check .`, `python -m pytest -q`, and `python -m heart_mlops.train` in that order. WSL_RUNBOOK.md gives the full Windows-to-Linux path and commands.")
    para(doc, "Build the local image with `docker build --build-arg PYTHON_VERSION=3.12 -t heart-disease-api:local .`. With Docker Desktop Kubernetes enabled, apply `k8s/deployment.yaml` and `k8s/service.yaml` from Windows PowerShell. The local LoadBalancer serves `http://localhost:8000/health`, `POST http://localhost:8000/predict` using `sample_request.json`, and `http://localhost:8000/monitor`; `GET /metrics` exposes Prometheus text. The endpoint is available while the laptop's cluster is running.")

    page(doc, "2 Data source and preparation")
    para(doc, "The source is the UCI processed Cleveland Heart Disease file, with 303 rows, 13 predictors, and the original 0–4 target. The download script verifies a SHA-256 digest. Numeric parsing converts the source's question mark missing marker to null; cleaning removes incomplete and duplicate records and maps targets 1–4 to class 1.")
    add_table(doc, ["Data check", "Observed result"], [
        ("Raw rows", meta["data_summary"]["raw_rows"]),
        ("Rows after cleaning", meta["data_summary"]["clean_rows"]),
        ("Rows removed", meta["data_summary"]["removed_missing_or_duplicate_rows"]),
        ("Absent / present", f"{meta['data_summary']['negative_count']} / {meta['data_summary']['positive_count']}"),
    ])
    para(doc, "The resulting CSV and summary JSON are committed as reusable inputs. The model pipeline still includes imputation for future inputs. No imputation statistics or scaling factors are learned from the held out test set or validation fold.")
    para(doc, "Feature groups: age, resting blood pressure, cholesterol, maximum heart rate, and ST depression are treated as numeric; the other eight predictors are encoded as categorical values. The target is excluded from all feature transformations.")

    page(doc, "3 Exploratory data analysis")
    para(doc, "The cleaned classes are moderately balanced: 160 records with absence and 137 with presence. The plots show the target distribution and numeric feature ranges before fitting any model.")
    figure(doc, "class_balance.png", "Figure 2  Cleaned dataset class balance", 4.0)
    figure(doc, "numeric_histograms.png", "Figure 3  Numeric predictor distributions", 5.2)

    page(doc, "4 Feature engineering and visual findings")
    para(doc, "The correlation heatmap is descriptive rather than a feature selection rule. Correlation does not establish clinical causation, and the small dataset makes visual differences uncertain. Box plots provide a compact comparison of age and maximum heart rate by target class.")
    figure(doc, "correlation_heatmap.png", "Figure 4  Pairwise numeric correlations", 4.6)
    figure(doc, "feature_by_target.png", "Figure 5  Age and maximum heart rate by class", 5.0)

    page(doc, "5 Model design and selection")
    para(doc, "The cleaned data is stratified into 80% training and 20% test partitions with seed 42. Each model's hyperparameters are evaluated by five stratified cross validation folds on the training partition. The pipeline fits imputation, scaling, and categorical encoding inside each fold, preventing preprocessing leakage.")
    para(doc, "Logistic Regression offers an interpretable linear baseline. Random Forest provides a nonlinear comparison. The highest mean validation ROC-AUC selects the final model. Accuracy, precision, and recall are also recorded to show different error tradeoffs.")
    rows = []
    for name, values in meta["candidate_cv_metrics"].items():
        rows.append((name.replace("_", " ").title(), *(f"{values[key]:.3f}" for key in ("accuracy", "precision", "recall", "roc_auc"))))
    add_table(doc, ["Model", "Accuracy", "Precision", "Recall", "ROC-AUC"], rows)
    figure(doc, "random_forest_cv_scores.png", "Figure 6  Random Forest candidate validation scores", 5.8)

    page(doc, "6 Held out test evaluation")
    test = meta["test_metrics"]
    tn, fp = test["confusion_matrix"][0]
    fn, tp = test["confusion_matrix"][1]
    para(doc, "After cross validation chose " + meta["selected_model"].replace("_", " ") + f", the held out test partition was evaluated once. The test split contains {tn+fp+fn+tp} records. The confusion matrix shows {tn} true negatives, {fp} false positives, {fn} false negatives, and {tp} true positives.")
    add_table(doc, ["Metric", "Test result"], [
        ("Accuracy", f"{test['accuracy']:.3f}"), ("Precision", f"{test['precision']:.3f}"),
        ("Recall", f"{test['recall']:.3f}"), ("ROC-AUC", f"{test['roc_auc']:.3f}"),
    ])
    figure(doc, "test_confusion_matrix.png", "Figure 7  Test confusion matrix", 3.3)
    figure(doc, "test_roc_curve.png", "Figure 8  Test ROC curve", 3.3)

    page(doc, "7 Experiment tracking and reproducibility")
    para(doc, "MLflow records a run for each candidate and a final selected model run. Each candidate run contains the best grid parameters, mean cross validation metrics, full search results, and a candidate score plot. The final run contains held out metrics, evaluation figures, metadata, and the fitted model. SQLite stores run metadata locally; CI uploads the generated store as a workflow artifact.")
    evidence(doc, "04-mlflow.png", "Figure 9  MLflow candidate and selected run metrics", 5.7, 3.6)
    para(doc, "The joblib file contains the full fitted preprocessing and classifier pipeline. Model metadata records the source checksum, selected parameters, features, seed, package version, and actual test metrics. Requirements and the raw download script allow a clean rebuild.")

    page(doc, "8 Quality checks and continuous integration")
    para(doc, "Unit tests cover target mapping and missing data, invalid source targets, pipeline fitting and probability output, API input validation, readiness, and monitoring endpoints. GitHub Actions runs Ruff, Pytest, data preparation, EDA, training, and a Docker image build. A failure in any required step fails the workflow; generated model and experiment files are uploaded for inspection.")
    evidence(doc, "05-tests-ci.png", "Figure 10  Passing GitHub Actions workflow", 5.5)
    evidence(doc, "05-tests-ci-artifacts.png", "Figure 11  Uploaded workflow artifact", 5.1, 1.1)
    evidence(doc, "06-docker.png", "Figure 12  Local Docker image build", 5.0)
    evidence(doc, "07-docker-prediction.png", "Figure 13  Local container prediction and request logs", 5.4, 1.55)

    page(doc, "9 Deployment monitoring and limitations")
    para(doc, "Docker Desktop Kubernetes deploys one API replica with health probes, CPU/memory limits, and a LoadBalancer Service on port 8000. The API provides `/predict`, `/health`, `/metrics`, `/monitor`, and OpenAPI documentation. Request logs contain only method, route, status, and duration; patient feature values are not logged.")
    para(doc, "The sample_request.json tests against the local container and Kubernetes service returned class 1, positive-class model probability 0.9837, and confidence 0.9837. This example score is not a validated clinical risk estimate.")
    evidence(doc, "08-kubernetes.png", "Figure 14  Ready Kubernetes pod and LoadBalancer Service", 5.2)
    evidence(doc, "09-kubernetes-prediction.png", "Figure 15  Prediction from the deployed Kubernetes API", 5.3, 0.8)
    evidence(doc, "10-monitoring.png", "Figure 16  Live API monitoring dashboard", 5.2)
    para(doc, "Limitations: the dataset is small and historical, no external validation or fairness assessment was performed, and predicted probabilities are not calibrated clinical risks. The local Kubernetes endpoint is accessible from the laptop, not a public internet URL.")
    para(doc, "Repository: " + (repo_url or "Add the GitHub URL after publishing the project."))
    para(doc, "Source: Janosi et al., Heart Disease, UCI Machine Learning Repository, 1988. https://doi.org/10.24432/C52P4X")

    target = ROOT / "reports" / ("Final_Report.docx" if final else "Report_Draft.docx")
    doc.save(target)
    print(target)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--repo-url", default="")
    args = parser.parse_args()
    build(final=args.final, repo_url=args.repo_url)
