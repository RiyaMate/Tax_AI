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

# Global dictionary to store the latest uploaded file URL
uploaded_files = {}

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)) -> Dict[str, str]:
    """
    Endpoint to upload a PDF file to AWS S3 and download locally
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no name")

    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET environment variable is missing")
    
    try:
        s3_client.upload_fileobj(file.file, S3_BUCKET, file.filename)
        file_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{file.filename}"

        # Store the file URL in a global dictionary
        uploaded_files[file.filename] = file_url
        
        # Download the file locally after upload
        local_path = os.path.join(os.getcwd(), file.filename)
        response = requests.get(file_url)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(response.content)
        
        return {"filename": file.filename, "message": "PDF uploaded and downloaded successfully!", "file_url": file_url, "local_path": local_path}
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/get-latest-file-url")
async def get_latest_file_url() -> Dict[str, str]:
    """
    Retrieve the most recently uploaded file's URL
    """
    if not uploaded_files:
        raise HTTPException(status_code=404, detail="No files have been uploaded yet")
    
    latest_filename = list(uploaded_files.keys())[-1]
    return {"filename": latest_filename, "file_url": uploaded_files[latest_filename]}
