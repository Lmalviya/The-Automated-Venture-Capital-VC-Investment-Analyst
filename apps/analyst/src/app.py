import os
import tempfile
from pathlib import Path
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import boto3
from botocore.config import Config

# Import the existing analyst pipeline code
from vs_analyst.orchestrator.pipeline import run_pipeline
from vs_analyst.schemas.state import AnalysisState
from vs_analyst.schemas.user_inputs import UserInputSchema, InvestmentStage

app = FastAPI(
    title="VC Investment Analyst Agent Service",
    description="Internal agent microservice that runs the LangGraph VC analyst pipeline",
    version="1.0.0"
)

# S3 / MinIO Configuration
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadminpassword")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "vc-analyst-decks")

# Initialize S3 Client configured for local MinIO
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1"
)

class AnalysisRequest(BaseModel):
    file_path: str = Field(..., description="MinIO file key for the pitch deck")
    startup_name: str = Field(..., description="Name of the startup")
    industry_sector: str = Field(..., description="E.g., SaaS, AI, HealthTech")
    funding_stage: str = Field(..., description="E.g., pre-seed, seed, series_a")
    requested_amount: float = Field(..., description="Amount raising")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/analyze", summary="Run investment analyst pipeline on pitch deck")
async def analyze_deck(request: AnalysisRequest):
    temp_file = None
    try:
        # 1. Fetch file from S3 / MinIO
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=request.file_path)
            file_bytes = response["Body"].read()
        except s3_client.exceptions.NoSuchKey:
            raise HTTPException(status_code=404, detail=f"File {request.file_path} not found in bucket {S3_BUCKET_NAME}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch file from S3: {str(e)}")

        # 2. Write file bytes to a temporary local file so the PDF/PPTX parsers can read it
        file_ext = os.path.splitext(request.file_path)[1] or ".pdf"
        temp_dir = tempfile.gettempdir()
        temp_file_path = Path(temp_dir) / f"deck_{request.startup_name.replace(' ', '_')}_{os.urandom(4).hex()}{file_ext}"
        
        with open(temp_file_path, "wb") as f:
            f.write(file_bytes)
        
        temp_file = temp_file_path

        # 3. Map the funding stage string to the InvestmentStage enum
        try:
            normalized_stage = request.funding_stage.upper().replace(" ", "_").replace("-", "_")
            stage_enum = InvestmentStage[normalized_stage]
        except KeyError:
            # Fallback to SEED if the string doesn't match
            stage_enum = InvestmentStage.SEED

        # 4. Prepare the LangGraph input schemas
        user_input = UserInputSchema(
            pitch_deck_path=temp_file_path,
            investment_stage=stage_enum,
            website_url=f"https://{request.startup_name.lower().replace(' ', '')}.com",
            sector=request.industry_sector
        )

        state = AnalysisState(
            run_id=f"api-run-{os.urandom(6).hex()}",
            user_input=user_input
        )

        # 5. Execute the pipeline
        final_state = await run_pipeline(state)

        # 6. Extract results from the final state to serialize as response
        # Using a fallback mock structure if pipeline didn't populate them fully
        company_data = final_state.company.model_dump() if final_state.company else {}
        market_data = final_state.market.model_dump() if final_state.market else {}
        founders_data = [f.model_dump() for f in final_state.founders] if final_state.founders else []
        finance_data = final_state.finance.model_dump() if final_state.finance else {}
        competitors_data = final_state.competitive.model_dump() if final_state.competitive else {}

        # Synthesize a high-level summary report for the user
        report = {
            "startup_name": request.startup_name,
            "status": final_state.status.value if hasattr(final_state.status, "value") else str(final_state.status),
            "metadata": {
                "sector": request.industry_sector,
                "stage": request.funding_stage,
                "requested_amount": request.requested_amount,
                "file_processed": request.file_path
            },
            "analysis": {
                "company_profile": company_data,
                "market_analysis": market_data,
                "founders": founders_data,
                "financial_metrics": finance_data,
                "competitive_landscape": competitors_data,
                "agent_run_statuses": final_state.agent_statuses
            }
        }

        return report

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")
    
    finally:
        # Cleanup the temp file
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
