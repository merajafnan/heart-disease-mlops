"""FastAPI inference service with request logs and live metrics."""

import json
import logging
import time
from collections import Counter
from threading import Lock

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Histogram, generate_latest
from prometheus_client import Counter as PromCounter
from pydantic import BaseModel, ConfigDict, Field

from heart_mlops.predict import load_model, predict_one

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("heart_mlops.api")
app = FastAPI(title="Heart Disease UCI Educational API", version="1.0.0")
REQUESTS = PromCounter("api_requests_total", "API requests", ["method", "path", "status"])
LATENCY = Histogram("api_request_duration_seconds", "API response time", ["path"])
_stats = Counter()
_stats_lock = Lock()


class PatientFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: int = Field(ge=1, le=120)
    sex: int = Field(ge=0, le=1)
    cp: int = Field(ge=1, le=4)
    trestbps: float = Field(gt=0)
    chol: float = Field(ge=0)
    fbs: int = Field(ge=0, le=1)
    restecg: int = Field(ge=0, le=2)
    thalach: float = Field(gt=0)
    exang: int = Field(ge=0, le=1)
    oldpeak: float
    slope: int = Field(ge=1, le=3)
    ca: int = Field(ge=0, le=4)
    thal: int = Field(ge=3, le=7)


@app.middleware("http")
async def log_request(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        duration = time.perf_counter() - start
        path = request.url.path if request.url.path in {
            "/predict", "/health", "/metrics", "/monitor", "/stats", "/docs", "/openapi.json"
        } else "other"
        REQUESTS.labels(request.method, path, str(status)).inc()
        LATENCY.labels(path).observe(duration)
        with _stats_lock:
            _stats["requests"] += 1
            _stats[f"status_{status}"] += 1
            if path == "/predict":
                _stats["prediction_requests"] += 1
            _stats["total_duration_seconds"] += duration
        logger.info(json.dumps({
            "event": "http_request", "method": request.method, "path": path,
            "status": status, "duration_ms": round(duration * 1000, 2),
        }))


@app.get("/health")
def health():
    try:
        load_model()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ready"}


@app.post("/predict")
def predict(features: PatientFeatures):
    try:
        return predict_one(features.model_dump())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/stats")
def stats():
    with _stats_lock:
        snapshot = dict(_stats)
    count = snapshot.get("requests", 0)
    snapshot["average_duration_ms"] = round(
        1000 * snapshot.get("total_duration_seconds", 0) / count, 2
    ) if count else 0
    return snapshot


@app.get("/monitor", response_class=HTMLResponse)
def monitor():
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Heart Disease API Monitoring</title><style>
body{font-family:system-ui,sans-serif;margin:2rem auto;max-width:760px;color:#17212b}
h1{font-size:1.7rem} .cards{display:grid;grid-template-columns:repeat(2,1fr);gap:1rem}
.card{padding:1rem;border:1px solid #cbd5e1;border-radius:10px;background:#f8fafc}
.value{font-size:1.8rem;font-weight:700}small{color:#475569}
</style></head><body><h1>Heart Disease API Monitoring</h1>
<p>Live counters from this API process. Refreshes every five seconds.</p>
<div class="cards" id="cards"></div><p><small>See /metrics for Prometheus data and
Docker or kubectl logs for structured request logs. No patient input is logged.</small></p>
<script>async function refresh(){const d=await(await fetch('/stats')).json();
const items=[['Requests',d.requests||0],['Predictions',d.prediction_requests||0],
['Successful responses',d.status_200||0],['Average latency (ms)',d.average_duration_ms||0]];
document.getElementById('cards').innerHTML=items.map(x=>
`<div class="card"><small>${x[0]}</small><div class="value">${x[1]}</div></div>`).join('');}
refresh();setInterval(refresh,5000);</script></body></html>"""

