from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import os
import boto3
from botocore.exceptions import NoCredentialsError

# AWS S3 Configuration
S3_BUCKET = os.getenv("S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Create FastAPI instance
app = FastAPI(
    title="Lab Demo API",
    description="Simple FastAPI application with health check and PDF upload to S3"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify the service is running
    """
    return {"status": "healthy", "message": "Service is running! All good!!!"}

@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint with basic service information
    """
    return {
        "service": "Lab Demo API",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/env-demo")
async def get_demo_env() -> Dict[str, str]:
    """
    Demo endpoint that returns an environment variable
    """
    demo_value = os.getenv("DEMO_VALUE", "default_value")
    return {"env_variable": "DEMO_VALUE", "value": demo_value}

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)) -> Dict[str, str]:
    """
    Endpoint to upload a PDF file to AWS S3
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        s3_client.upload_fileobj(file.file, S3_BUCKET, file.filename)
        file_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{file.filename}"
        return {"filename": file.filename, "message": "PDF uploaded successfully!", "file_url": file_url}
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))