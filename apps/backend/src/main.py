import os
import time
import uuid
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import boto3
from botocore.config import Config
import httpx

app = FastAPI(
    title="Automated VC Investment Analyst API Gateway",
    description="REST API Gateway entry point for Phase-1 Investment Analysis",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# S3 / MinIO Configuration
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
# S3_ENDPOINT_URL_EXTERNAL is what the browser client sees (typically http://localhost:9000 for local docker compose)
S3_ENDPOINT_URL_EXTERNAL = os.getenv("S3_ENDPOINT_URL_EXTERNAL", S3_ENDPOINT_URL)
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadminpassword")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "vc-analyst-decks")

# Service URLs
ANALYST_SERVICE_URL = os.getenv("ANALYST_SERVICE_URL", "http://localhost:8001")

# Internal client for server-to-server operations (like checking file exists)
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1"
)

# External client for generating presigned URLs that the client browser must resolve
s3_client_external = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL_EXTERNAL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1"
)

@app.on_event("startup")
def initialize_s3_resources():
    # 0. Wait for MinIO container to be ready and accepting requests
    max_retries = 15
    retry_delay = 2
    for attempt in range(1, max_retries + 1):
        try:
            s3_client.list_buckets()
            print(f"Connected to MinIO successfully on attempt {attempt}.")
            break
        except Exception as e:
            print(f"Waiting for MinIO/S3 service to start... (Attempt {attempt}/{max_retries}) - Error: {e}")
            if attempt == max_retries:
                print("Failed to connect to MinIO/S3 after max retries. Resource initialization aborted.")
                return
            time.sleep(retry_delay)

    try:
        # 1. Proactively ensure the target bucket exists
        try:
            s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        except Exception:
            print(f"Bucket {S3_BUCKET_NAME} does not exist. Creating bucket...")
            s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
            print(f"Bucket {S3_BUCKET_NAME} created successfully.")
        
        # 2. Automatically configure CORS to allow direct PUT uploads from the frontend browser
        try:
            s3_client.put_bucket_cors(
                Bucket=S3_BUCKET_NAME,
                CORSConfiguration={
                    'CORSRules': [
                        {
                            'AllowedHeaders': ['*'],
                            'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                            'AllowedOrigins': ['*'],
                            'MaxAgeSeconds': 3000
                        }
                    ]
                }
            )
            print(f"Successfully configured direct-upload CORS policy on bucket {S3_BUCKET_NAME}.")
        except Exception as cors_err:
            print(f"Notice: Bucket CORS configuration not applied ({cors_err}). This is normal for local MinIO where CORS is enabled globally by default.")
    except Exception as e:
        print(f"Warning: Local S3 initialization failed: {e}")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/upload-url", summary="Generate a secure temporary upload URL")
def get_upload_url(
    filename: str = Query(..., description="The name of the file to upload"),
    content_type: str = Query(..., description="The MIME type of the file, e.g. application/pdf")
):
    try:
        # Generate a unique key to prevent filename collisions
        unique_id = uuid.uuid4().hex
        file_extension = os.path.splitext(filename)[1] or ".pdf"
        file_key = f"temp-uploads/{unique_id}{file_extension}"

        # Generate the presigned PUT URL using the external client
        presigned_url = s3_client_external.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": file_key,
                "ContentType": content_type
            },
            ExpiresIn=900  # URL valid for 15 minutes (900 seconds)
        )

        return {
            "presigned_url": presigned_url,
            "file_path": file_key  # Send this key with your post payload
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")

class InvestmentAnalysisPayload(BaseModel):
    file_path: str = Field(..., description="The temporary storage file path from MinIO/S3")
    startup_name: str = Field(..., description="Name of the startup")
    industry_sector: str = Field(..., description="E.g., SaaS, FinTech, Web3, Biotech")
    funding_stage: str = Field(..., description="E.g., Pre-Seed, Seed, Series A")
    requested_amount: float = Field(..., description="Target funding raising goal")

@app.post("/api/v1/analyze-investment", summary="Submit investment pitch deck and start analysis")
async def analyze_investment(payload: InvestmentAnalysisPayload):
    try:
        # Forward request to the internal analyst service
        async with httpx.AsyncClient(timeout=180.0) as client:
            analyst_payload = {
                "file_path": payload.file_path,
                "startup_name": payload.startup_name,
                "industry_sector": payload.industry_sector,
                "funding_stage": payload.funding_stage,
                "requested_amount": payload.requested_amount
            }
            
            response = await client.post(
                f"{ANALYST_SERVICE_URL}/api/v1/analyze",
                json=analyst_payload
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Analyst service failed: {response.text}"
                )
                
            return response.json()
            
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Analyst agent service is currently unreachable.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gateway routing error: {str(e)}")
