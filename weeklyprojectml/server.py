"""
FastAPI High-Performance Web Server for Bank Loan Approval Prediction.
Designed for ultra-fast page loads (<150ms), zero WebSocket overhead,
instantaneous AJAX inference (<10ms), and 24/7 deployment resilience.
"""

import json
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.predict import load_pipeline, predict_loan

# Directories
STATIC_DIR = PROJECT_ROOT / "static"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
METRICS_PATH = PROJECT_ROOT / "outputs" / "metrics" / "model_metrics.json"
INDEX_HTML = TEMPLATES_DIR / "index.html"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Initialize FastAPI App
app = FastAPI(
    title="Bank Loan Approval Prediction API",
    description="High-performance machine learning inference engine for credit risk assessment.",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and figures
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
if FIGURES_DIR.exists():
    app.mount("/figures", StaticFiles(directory=str(FIGURES_DIR)), name="figures")

# Pre-load ML pipeline into memory at startup
try:
    ml_pipeline = load_pipeline()
    print("Model pipeline successfully loaded into server memory.")
except Exception as e:
    ml_pipeline = None
    print(f"Notice: Model pipeline not found or not yet trained: {e}")


# Input Schema
class LoanApplicantInput(BaseModel):
    Gender: str = Field(default="Male")
    Married: str = Field(default="Yes")
    Dependents: str = Field(default="1")
    Education: str = Field(default="Graduate")
    Self_Employed: str = Field(default="No")
    ApplicantIncome: float = Field(default=5000.0, ge=0)
    CoapplicantIncome: float = Field(default=1800.0, ge=0)
    LoanAmount: float = Field(default=130.0, gt=0)
    Loan_Amount_Term: float = Field(default=360.0, gt=0)
    Credit_History: float = Field(default=1.0)
    Property_Area: str = Field(default="Semiurban")


@app.get("/")
async def serve_dashboard():
    """Serves the fast, responsive single-page web dashboard."""
    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML), media_type="text/html")
    alt_path = PROJECT_ROOT / "index.html"
    if alt_path.exists():
        return FileResponse(str(alt_path), media_type="text/html")
    return HTMLResponse("<h1>Bank Loan Approval Prediction System</h1>", status_code=200)


@app.get("/api/health")
async def health_check():
    """
    Lightweight keep-alive heartbeat endpoint.
    Use with free monitoring services (e.g. UptimeRobot) to prevent free-tier cloud sleep.
    """
    return {
        "status": "healthy",
        "service": "Bank Loan Approval Prediction System",
        "model_loaded": ml_pipeline is not None,
    }


@app.get("/api/metrics")
async def get_metrics():
    """Returns genuine model evaluation comparison metrics."""
    if METRICS_PATH.exists():
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            return JSONResponse(content=json.load(f))
    raise HTTPException(status_code=404, detail="Metrics not yet generated.")


@app.post("/api/predict")
async def predict_loan_endpoint(applicant: LoanApplicantInput):
    """
    Executes real-time inference in <10ms and returns
    approval probability, risk classification, and key indicators.
    """
    global ml_pipeline
    if ml_pipeline is None:
        try:
            ml_pipeline = load_pipeline()
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="ML pipeline artifact not found. Please run 'python src/train.py' first.",
            )

    try:
        input_dict = applicant.model_dump()
        result = predict_loan(input_dict, pipeline=ml_pipeline)
        return JSONResponse(content=result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(exc)}")


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting ultra-fast Loan Prediction Server on http://0.0.0.0:{port} ...")
    uvicorn.run("server:app", host="0.0.0.0", port=port)
