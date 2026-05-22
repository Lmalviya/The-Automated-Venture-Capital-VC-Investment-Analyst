import uuid
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional

from vs_analyst import get_logger, setup_logging
from vs_analyst.schemas.user_inputs import InvestmentStage
from service.analysis import AnalysisService, AnalysisRequest

# Initialize structured logging on application load
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="VC Investment Analyst Agent Service",
    description="Internal agent microservice that runs the LangGraph VC analyst pipeline",
    version="1.0.0"
)

# Instantiate the service layer orchestrator
analysis_service = AnalysisService()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/analyze", status_code=202, summary="Run investment analyst pipeline on pitch deck")
async def analyze_deck(request: AnalysisRequest, background_tasks: BackgroundTasks):
    
    # 1. Validate file format extension (.pdf or .pptx)
    _, ext = os.path.splitext(request.file_path.lower())
    if not ext:
        logger.warning("Rejected request due to missing file extension", file_path=request.file_path)
        raise HTTPException(
            status_code=400,
            detail="The provided file key has no file extension. Only .pdf and .pptx files are supported."
        )
    if ext not in (".pdf", ".pptx"):
        logger.warning("Rejected request due to invalid file format", file_path=request.file_path)
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Only .pdf and .pptx files are supported."
        )

    # 2. Validate funding stage strictly if provided
    if request.funding_stage is not None:
        try:
            InvestmentStage.from_str(request.funding_stage)
        except ValueError as e:
            logger.warning("Rejected request due to invalid investment stage", provided_stage=request.funding_stage, error=str(e))
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )

    # 3. Establish Distributed Tracing ID (Run ID)
    run_id = request.run_id or str(uuid.uuid4())
    logger.info("Registering background analysis pipeline", run_id=run_id, startup=request.startup_name)

    # 4. Schedule non-blocking execution in background thread
    background_tasks.add_task(
        analysis_service.execute_analysis,
        run_id=run_id,
        file_path=request.file_path,
        startup_name=request.startup_name,
        industry_sector=request.industry_sector,
        funding_stage=request.funding_stage,
        requested_amount=request.requested_amount
    )

    # 4. Return immediately to the caller
    return {
        "run_id": run_id,
        "status": "processing",
        "message": "Analysis pipeline successfully queued."
    }

