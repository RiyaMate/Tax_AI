from fastapi import FastAPI, UploadFile, File, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional, List
import gc
from pydantic import BaseModel
import os
import sys
from google.cloud import storage
import fitz
import requests
import uuid
from dotenv import load_dotenv
load_dotenv(override=True)
print("GEMINI_API_KEY loaded in main.py:", os.getenv("GEMINI_API_KEY"))
from fastapi import Query
from datetime import datetime
MAX_FILE_SIZE_MB = 5  # Max allowed file size in MB
MAX_PAGE_COUNT = 5  # Max allowed pages
import time
import redis
import json
import shutil
import asyncio
import tempfile
# Add the root directory to the Python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# Add the api directory to Python path as well (since PDF_Extraction_and_Markdown_Generation is in api/)
api_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(api_dir)

# Import docling extraction with graceful fallback for scipy/sklearn conflicts
try:
    from docklingextraction import main as docling_main
    DOCLING_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Docling extraction unavailable: {e}")
    print("[INFO] Continuing without docling support (using LandingAI only)")
    DOCLING_AVAILABLE = False
    docling_main = None

from logger import api_logger, pdf_logger, gcs_logger, error_logger, request_logger, log_request, log_error
from llm_extractor.litellm_query_generator import MODEL_CONFIGS
import threading
from worker import main as worker_main
# Load environment variables from .env file
load_dotenv(override=True)
print("[DEBUG] VISION_AGENT_API_KEY at startup:", os.getenv("VISION_AGENT_API_KEY"))

# Google Cloud Storage Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
gcs_client = storage.Client(project=GCP_PROJECT_ID)
gcs_bucket = gcs_client.bucket(GCS_BUCKET_NAME)

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Redis client with proper error handling
redis_client = None
try:
    import redis
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=5
    )
    redis_client.ping()  # Test the connection
    api_logger.info(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    api_logger.error(f"Redis connection failed: {str(e)}")
    api_logger.warning("Application will run without Redis functionality")
    # Set to None so we can check if Redis is available later
    redis_client = None

# Stream names
SUMMARY_STREAM = "summary_requests"
QUESTION_STREAM = "question_requests"
RESULT_STREAM = "llm_results"

# Create FastAPI instance
app = FastAPI(
    title="Lab Demo API",
    description="Simple FastAPI application with health check and PDF upload to S3"
)

class ScrapeRequest(BaseModel):
    url: str

# LLM Request Models
class SummaryRequest(BaseModel):
    request_id: str
    content: str
    model: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7

class QuestionRequest(BaseModel):
    request_id: str
    content: str
    question: str
    model: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7

class LLMModelsResponse(BaseModel):
    models: List[str]

class SummarizeRequest(BaseModel):
    request_id: str
    content: str
    model: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    content_type: Optional[str] = "markdown"

# In-memory results cache
llm_results = {}


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

latest_file_details = []
#Add a middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request,call_next):
    request_id = str(uuid.uuid4())
    request_path = request.url.path
    request_method = request.method
    client_host = request.client.host if request.client else "unknown"
    log_request(f"Request ID: {request_id} - {request_method} - {request_path} - Client: {client_host}")
    
    start_time  =  time.time()
    response  = await call_next(request)
    process_time = time.time() - start_time
    log_request(f"Request ID: {request_id} - Process Time: {process_time:.2f} seconds")
    return response



def check_pdf_constraints(pdf_path):
    """
    Check if the PDF meets the file size and page count constraints.
    """
    try:
        # Get file size
        pdf_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)  # Convert bytes to MB

        # Get page count
        with fitz.open(pdf_path) as pdf_doc:
            pdf_page_count = len(pdf_doc)

        if pdf_size_mb > MAX_FILE_SIZE_MB:
            error_message = f"[FAIL] File too large: {pdf_size_mb:.2f}MB (Limit: {MAX_FILE_SIZE_MB}MB). Process stopped."
            pdf_logger.warning(error_message)
            return {"error": error_message}  # Return error instead of raising

        if pdf_page_count > MAX_PAGE_COUNT:
            error_message = f"[FAIL] Too many pages: {pdf_page_count} pages (Limit: {MAX_PAGE_COUNT} pages). Process stopped."
            pdf_logger.warning(error_message)
            return {"error": error_message}  # Return error instead of raising

        pdf_logger.info(f"[YES] PDF meets size ({pdf_size_mb:.2f}MB) and page count ({pdf_page_count} pages) limits. Proceeding with upload...")
        return {"success": True}

    except Exception as e:
        log_error(f"Failed to check PDF constraints: {str(e)}")
        return {"error": f"Failed to check PDF constraints: {str(e)}"}
    
@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint with basic service information
    """
    api_logger.info("Root endpoint accessed")
    return {
        "service": "Lab Demo API",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/debug/gcs-contents")
async def debug_gcs_contents():
    """
    Debug endpoint to list all contents in GCS bucket
    """
    try:
        api_logger.info(f"Listing all objects in bucket: {GCS_BUCKET_NAME}")
        
        all_blobs = list(gcs_client.list_blobs(GCS_BUCKET_NAME))
        api_logger.info(f"Total objects in bucket: {len(all_blobs)}")
        
        # Group by prefix
        items = {
            "total_count": len(all_blobs),
            "prefixes": {},
            "sample_files": []
        }
        
        for blob in all_blobs[:20]:  # Show first 20
            prefix = blob.name.split("/")[0] if "/" in blob.name else "root"
            if prefix not in items["prefixes"]:
                items["prefixes"][prefix] = 0
            items["prefixes"][prefix] += 1
            items["sample_files"].append({
                "name": blob.name,
                "size": blob.size,
                "updated": blob.updated.isoformat() if blob.updated else None
            })
        
        return items
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}

@app.get("/debug/markdown-outputs")
async def debug_markdown_outputs():
    """
    Debug endpoint to specifically check markdown_outputs folder
    """
    try:
        gcs_base_folder = "pdf_processing_pipeline/markdown_outputs/"
        api_logger.info(f"Listing objects in: {gcs_base_folder}")
        
        # List with delimiter to see folder structure
        blobs_iterator = gcs_client.list_blobs(GCS_BUCKET_NAME, prefix=gcs_base_folder, delimiter='/')
        blobs_list = list(blobs_iterator)
        prefixes = list(blobs_iterator.prefixes) if hasattr(blobs_iterator, 'prefixes') else []
        
        api_logger.info(f"Blobs found: {len(blobs_list)}, Prefixes: {len(prefixes)}")
        
        return {
            "base_folder": gcs_base_folder,
            "blobs_count": len(blobs_list),
            "prefixes_count": len(prefixes),
            "prefixes": prefixes,
            "blobs": [{"name": b.name, "size": b.size} for b in blobs_list[:10]]
        }
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}
# Start the worker process on application startup
@app.on_event("startup")
async def startup_event():
    # Start the worker process in the background
    worker_thread = threading.Thread(target=start_worker_process, daemon=True)
    worker_thread.start()
    api_logger.info("LLM worker process started in background thread")

# Background task to listen for LLM results from Redis and update the cache
@app.on_event("startup")
async def start_result_listener():
    """
    Start a background task that listens for new results in the Redis stream
    and updates the in-memory cache.
    """
    # Skip if Redis isn't available
    if redis_client is None:
        api_logger.warning("Redis not available - result listener not started")
        return
    
    async def listen_for_results():
        # Create consumer group if it doesn't exist
        try:
            redis_client.xgroup_create(RESULT_STREAM, "fastapi_listeners", mkstream=True)
        except redis.exceptions.ResponseError as e:
            # Group likely already exists
            api_logger.info(f"Consumer group already exists: {str(e)}")
        except Exception as e:
            api_logger.error(f"Error creating consumer group: {str(e)}")
            return
        
        api_logger.info("Started Redis result listener")
        
        while True:
            try:
                # Your Redis processing code here
                pass
            except Exception as e:
                api_logger.error(f"Error in result listener: {str(e)}")
            
            # Wait a bit before next poll
            await asyncio.sleep(1)
    
    # Start the listener task
    asyncio.create_task(listen_for_results())


# [YES] Favicon Route
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), service_type: str = Query("")) -> Dict[str, str]:
    """
    Uploads a PDF file to Google Cloud Storage after checking constraints.
    """
    pdf_logger.info(f"PDF upload requested : {file.filename},Service type: {file.content_type}")
    if file.content_type != "application/pdf":
        pdf_logger.warning(f"Invalid file type attempted: {file.content_type}")
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    if not file.filename:
        pdf_logger.warning("Upload attempted with no filename")
        raise HTTPException(status_code=400, detail="Uploaded file has no name")

    if not GCS_BUCKET_NAME:
        log_error("GCS_BUCKET_NAME environment variable is missing")
        raise HTTPException(status_code=500, detail="GCS_BUCKET_NAME environment variable is missing")
    
    temp_pdf_path = None  # Define temp path for cleanup

    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(file.file.read())
            temp_pdf_path = temp_pdf.name
        pdf_logger.info(f"PDF temporarily saved to: {temp_pdf_path}")

        # Check PDF constraints for only Enterprise service type
        if service_type == "Enterprise":
            pdf_logger.info(f"Checking Enterprise constraints for {file.filename}")
            constraint_check = check_pdf_constraints(temp_pdf_path)
            if "error" in constraint_check:
                pdf_logger.warning(f"PDF failed constraint check: {constraint_check['error']}")
                os.remove(temp_pdf_path)  # Cleanup temp file
                raise HTTPException(status_code=400, detail=constraint_check["error"])

        # Upload file to GCS (only if constraints are met)
        gcs_key = f"RawInputs/{file.filename}"
        gcs_logger.info(f"Uploading PDF to GCS: {gcs_key}")
        blob = gcs_bucket.blob(gcs_key)
        blob.upload_from_filename(temp_pdf_path)
        gcs_logger.info(f"PDF successfully uploaded to GCS: gs://{GCS_BUCKET_NAME}/{gcs_key}")

        gcs_logger.debug(f"Generated blob reference for {gcs_key}")
        # Cleanup: Delete the temp file after successful upload
        os.remove(temp_pdf_path)
        pdf_logger.debug(f"Temporary PDF file deleted: {temp_pdf_path}")
        # Save the file details globally
        new_file_details = {
            "filename": file.filename,
            "gcs_key": gcs_key,
            "upload_time": str(time.time())
        }
        latest_file_details.append(new_file_details)
        pdf_logger.info(f"File details saved for {file.filename}")
        return {"filename": file.filename, "message": "[YES] PDF uploaded successfully!"}

    except HTTPException as e:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)  # Cleanup on error
        raise e
    except Exception as e:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)  # Cleanup on error
        log_error(f"PDF upload failed for {file.filename}", e)
        raise HTTPException(status_code=500, detail=f"[FAIL] Upload failed: {str(e)}")
        
@app.get("/get-latest-file-url")
async def get_latest_file_url() -> Dict[str, Any]:
    """
    Retrieve the most recently uploaded file's URL, download it locally, and save the details.
    """
    from datetime import timedelta
    api_logger.info("Fetching latest file URL")
    if not latest_file_details:
        api_logger.warning("No files have been uploaded yet")
        raise HTTPException(status_code=404, detail="No files have been uploaded yet")
    
    current_file = latest_file_details[-1]
    api_logger.info(f"Latest file: {current_file['filename']}")
    
    # Get the GCS key from stored details
    gcs_key = current_file["gcs_key"]
    
    try:
        # Generate a signed URL for the blob (works with private buckets)
        blob = gcs_bucket.blob(gcs_key)
        fresh_file_url = blob.generate_signed_url(version="v4", expiration=timedelta(hours=1))
        
        # Update the URL in our stored details
        current_file["file_url"] = fresh_file_url
        gcs_logger.info(f"Generated signed URL for {gcs_key}")
        
        # Define local download path
        project_root = os.getcwd()
        downloaded_pdf_path = os.path.join(project_root, current_file["filename"])

        # Download the file using the signed URL
        pdf_logger.info(f"Downloading file from: {fresh_file_url}")
        response = requests.get(fresh_file_url)
        response.raise_for_status()
        
        with open(downloaded_pdf_path, "wb") as pdf_file:
            pdf_file.write(response.content)
        
        pdf_logger.info(f"PDF downloaded successfully to: {downloaded_pdf_path}")
        
        # Update the local path in the global file details
        current_file["local_path"] = downloaded_pdf_path
        pdf_logger.debug(f"Updated local path in file details: {downloaded_pdf_path}")
        
    except requests.exceptions.RequestException as e:
        log_error(f"Failed to download PDF: {current_file['filename']}", e)
        raise HTTPException(status_code=500, detail=f"Failed to download PDF: {str(e)}")
    except Exception as e:
        log_error(f"Error in get_latest_file_url: {str(e)}", e)
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")

    return current_file

@app.post("/convert-pdf-to-markdown")
async def convert_pdf_to_markdown(file: UploadFile = File(...)):
    pdf_logger.info(f"Starting PDF to Markdown conversion for: {file.filename}")
    # Create a temporary file path
    temp_dir = tempfile.mkdtemp()
    try:
        temp_pdf_path = os.path.join(temp_dir, "temp.pdf")
        
        # Write file to disk in chunks instead of loading all at once
        with open(temp_pdf_path, "wb") as pdf_file:
            while chunk := await file.read(1024 * 1024):  # Read 1MB chunks
                pdf_file.write(chunk)
        
        pdf_logger.info(f"PDF written to temp file: {temp_pdf_path}")
        
        # Process PDF page by page instead of all at once
        markdown_content = ""
        with fitz.open(temp_pdf_path) as pdf:
            page_count = len(pdf)
            pdf_logger.info(f"PDF has {page_count} pages")
            for page_num in range(page_count):
                page = pdf[page_num]
                text = page.get_text()
                # Process text to markdown
                markdown_content += f"## Page {page_num + 1}\n\n{text}\n\n"
                
                # Force garbage collection after each page
                page = None
                gc.collect()
        
        pdf_logger.info(f"Markdown conversion completed. Content length: {len(markdown_content)}")
        
        # Save markdown to GCS in the proper folder structure
        if GCS_BUCKET_NAME:
            try:
                from datetime import datetime, timedelta
                
                # Create a job-specific folder with timestamp
                job_id = str(uuid.uuid4())[:8]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                job_folder = f"pdf_processing_pipeline/markdown_outputs/{job_id}_{timestamp}/"
                
                # Create two versions: standard markdown and with-images version
                base_filename = file.filename.replace(".pdf", "")
                
                # Standard markdown file
                standard_md_key = f"{job_folder}{base_filename}.md"
                blob_standard = gcs_bucket.blob(standard_md_key)
                blob_standard.upload_from_string(markdown_content, content_type="text/markdown")
                gcs_logger.info(f"Standard markdown saved to GCS: {standard_md_key}")
                
                # With-images version (for consistency with other endpoints)
                with_images_md_key = f"{job_folder}{base_filename}-with-images.md"
                blob_with_images = gcs_bucket.blob(with_images_md_key)
                blob_with_images.upload_from_string(markdown_content, content_type="text/markdown")
                gcs_logger.info(f"Markdown with-images version saved to GCS: {with_images_md_key}")
                
                # Generate signed URLs for both versions
                standard_url = blob_standard.generate_signed_url(version="v4", expiration=timedelta(hours=1))
                with_images_url = blob_with_images.generate_signed_url(version="v4", expiration=timedelta(hours=1))
                
                gcs_logger.info(f"Successfully created markdown files in folder: {job_folder}")
                
                return {
                    "markdown": markdown_content,
                    "gcs_locations": {
                        "standard": standard_md_key,
                        "with_images": with_images_md_key
                    },
                    "signed_urls": {
                        "standard": standard_url,
                        "with_images": with_images_url
                    },
                    "job_id": job_id,
                    "message": "[YES] Markdown conversion completed and saved to GCS"
                }
            except Exception as e:
                gcs_logger.error(f"Failed to save markdown to GCS: {str(e)}", exc_info=True)
                pdf_logger.error(f"GCS save failed: {str(e)}")
                # Still return the markdown content even if GCS save fails
                return {
                    "markdown": markdown_content,
                    "warning": f"Markdown converted but GCS save failed: {str(e)}"
                }
        
        return {"markdown": markdown_content}
    finally:
        # Clean up temporary files
        shutil.rmtree(temp_dir, ignore_errors=True)
        pdf_logger.info(f"Cleaned up temp directory: {temp_dir}")

@app.get("/fetch-latest-markdown-urls")
async def fetch_latest_markdown_from_gcs():
    """
    Fetch Markdown file URLs from the latest job-specific subfolder in GCS.
    """
    from datetime import timedelta
    api_logger.info("Fetching latest markdown URLs from GCS")
    try:
        # Base folder where markdowns are stored
        gcs_base_folder = "pdf_processing_pipeline/markdown_outputs/"
        gcs_logger.info(f"Checking GCS folder: {gcs_base_folder}")

        # List ALL markdown files (without delimiter)
        all_markdown_blobs = list(gcs_client.list_blobs(GCS_BUCKET_NAME, prefix=gcs_base_folder))
        gcs_logger.info(f"Found {len(all_markdown_blobs)} total markdown files in GCS")

        if not all_markdown_blobs:
            api_logger.info("No markdown folders found in GCS - returning empty result")
            return {
                "message": "No markdown files have been generated yet. Upload and process a PDF first.",
                "latest_folder": None,
                "markdown_files": []
            }

        # Find the latest file by modification time
        latest_blob = max(all_markdown_blobs, key=lambda b: b.updated if b.updated else b.time_created)
        latest_folder = "/".join(latest_blob.name.split("/")[:-1]) + "/"

        gcs_logger.info(f"Latest folder identified: {latest_folder}")

        # Fetch all markdown files inside the latest folder
        latest_blobs = [
            blob for blob in all_markdown_blobs 
            if blob.name.startswith(latest_folder) and blob.name.endswith(".md")
        ]
        
        markdown_urls = []
        for blob in latest_blobs:
            signed_url = blob.generate_signed_url(version="v4", expiration=timedelta(hours=1))
            markdown_urls.append(signed_url)
        
        gcs_logger.info(f"Found {len(markdown_urls)} markdown files in the latest folder")

        return {
            "message": f"Fetched Markdown files from the latest subfolder: {latest_folder}",
            "latest_folder": latest_folder,
            "markdown_files": markdown_urls
        }

    except Exception as e:
        log_error("Failed to fetch markdown URLs from GCS", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch markdown files: {str(e)}")

@app.get("/fetch-latest-markdown-downloads")
async def fetch_latest_markdown_downloads():
    """
    Fetch Markdown file download links from the latest job-specific folder in GCS.
    """
    from datetime import timedelta
    api_logger.info("Fetching latest markdown downloads from GCS")

    try:
        # Base GCS folder where markdowns are stored
        gcs_base_folder = "pdf_processing_pipeline/markdown_outputs/"
        gcs_logger.info(f"Checking GCS folder: {gcs_base_folder}")

        # List ALL markdown files (without delimiter to get actual files)
        all_markdown_blobs = list(gcs_client.list_blobs(GCS_BUCKET_NAME, prefix=gcs_base_folder))
        gcs_logger.info(f"Found {len(all_markdown_blobs)} total markdown files in GCS")
        
        if not all_markdown_blobs:
            api_logger.info("No markdown files found in GCS - returning empty result")
            return {
                "message": "No markdown files have been generated yet. Upload and process a PDF first.",
                "latest_folder": None,
                "markdown_downloads": []
            }

        # Find the latest file by modification time
        latest_blob = max(all_markdown_blobs, key=lambda b: b.updated if b.updated else b.time_created)
        latest_folder = "/".join(latest_blob.name.split("/")[:-1]) + "/"
        
        gcs_logger.info(f"Latest folder identified: {latest_folder}")

        # Get all markdown files from the latest folder
        latest_folder_blobs = [
            blob for blob in all_markdown_blobs 
            if blob.name.startswith(latest_folder) and blob.name.endswith(".md")
        ]
        
        gcs_logger.info(f"Found {len(latest_folder_blobs)} markdown files in latest folder: {latest_folder}")
        
        if not latest_folder_blobs:
            api_logger.info("No markdown files found in the latest folder - returning empty result")
            return {
                "message": "No markdown files in the latest folder. Upload and process a PDF first.",
                "latest_folder": latest_folder,
                "markdown_downloads": []
            }

        # [YES] Generate signed download URLs for the markdown files
        markdown_download_links = []
        for blob in latest_folder_blobs:
            gcs_logger.info(f"Generating download link for: {blob.name}")
            # [YES] Use GCS signed URL (v4) for private files
            download_url = blob.generate_signed_url(version="v4", expiration=timedelta(hours=1))
            markdown_download_links.append({
                "file_name": blob.name.split("/")[-1],
                "file_key": blob.name,
                "download_url": download_url
            })
            gcs_logger.info(f"Download link generated for: {blob.name}")

        return {
            "message": f"Fetched Markdown downloads from the latest subfolder: {latest_folder}",
            "latest_folder": latest_folder,
            "markdown_downloads": markdown_download_links
        }

    except Exception as e:
        log_error("Failed to fetch markdown downloads from GCS", e)
        gcs_logger.error(f"DEBUG: Exception details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch markdown downloads: {str(e)}")
    
@app.get("/list-image-ref-markdowns")
async def list_image_ref_markdowns():
    """
    Fetch all Markdown files with 'image-ref' suffix from all subfolders in GCS and generate download links.
    """
    from datetime import timedelta
    api_logger.info("Fetching image-ref markdown files from all folders in GCS")

    try:
        # Base GCS folder where markdowns are stored
        gcs_base_folder = "pdf_processing_pipeline/markdown_outputs/"
        gcs_logger.info(f"Checking GCS base folder: {gcs_base_folder}")

        # Fetch all job subfolders
        blobs = gcs_client.list_blobs(GCS_BUCKET_NAME, prefix=gcs_base_folder, delimiter='/')
        subfolders = list(blobs.prefixes)
        gcs_logger.info(f"Found {len(subfolders)} markdown subfolders in GCS")

        if not subfolders:
            api_logger.info("No markdown folders found in GCS - returning empty result")
            return {
                "message": "No markdown files have been generated yet. Upload and process a PDF first.",
                "file_count": 0,
                "folder_count": 0,
                "image_ref_markdowns": []
            }

        # Collect all image-ref markdown files from all folders
        image_md_files = []

        for folder in subfolders:
            gcs_logger.info(f"Searching for image-ref markdowns in folder: {folder}")
            folder_blobs = gcs_client.list_blobs(GCS_BUCKET_NAME, prefix=folder)
            
            # Filter for markdown files with image-ref in their name
            for blob in folder_blobs:
                file_name = blob.name
                file_basename = file_name.split("/")[-1]
                
                if file_name.endswith(".md") and "-with-images." in file_basename:
                    gcs_logger.info(f"Found markdown with images: {file_name}")
                    
                    # Generate signed URL for the file
                    signed_blob = gcs_bucket.blob(file_name)
                    download_url = signed_blob.generate_signed_url(version="v4", expiration=timedelta(hours=1))
                    
                    # Add to our collection
                    image_md_files.append({
                        "folder": folder,
                        "file_name": file_basename,
                        "file_key": file_name,
                        "download_url": download_url,
                        "last_modified": blob.updated.isoformat()
                    })
                    
                    gcs_logger.info(f"Generated download link for: {file_name}")

        if not image_md_files:
            api_logger.info("No image-ref markdown files found in any folder - returning empty result")
            return {
                "message": "No image-ref markdown files found yet. Process a PDF with image extraction.",
                "file_count": 0,
                "folder_count": len(subfolders),
                "image_ref_markdowns": []
            }

        # Sort by last modified date (newest first)
        image_md_files.sort(key=lambda x: x["last_modified"], reverse=True)
        
        return {
            "message": f"Found {len(image_md_files)} image-ref markdown files across {len(subfolders)} folders",
            "file_count": len(image_md_files),
            "folder_count": len(subfolders),
            "image_ref_markdowns": image_md_files
        }

    except Exception as e:
        log_error("Failed to fetch image-ref markdown files from GCS", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch image-ref markdown files: {str(e)}")
# llm endpoints starts here
def start_worker_process():
    """
    Start the LLM worker process using asyncio in a separate thread
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(worker_main())
    loop.close()

@app.post("/summarize", status_code=202)
async def summarize_content(request: SummaryRequest):
    """
    Submit content for summarization by an LLM through Redis streams.
    Returns a 202 Accepted response with the request ID for polling results.
    """
    api_logger.info(f"Summary request received for model: {request.model}")
    try:
        # Add message to Redis summary stream
        data = {
            "request_id": request.request_id,
            "content": request.content,
            "model": request.model,
            "max_tokens": str(request.max_tokens),
            "temperature": str(request.temperature),
            "timestamp": str(time.time())
        }
        
        # Push to Redis stream
        redis_client.xadd(SUMMARY_STREAM, data)
        api_logger.info(f"Summary request {request.request_id} pushed to Redis stream")
        
        return {"request_id": request.request_id, "status": "processing"}
    except Exception as e:
        log_error(f"Failed to submit summary request", e)
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")

@app.post("/ask-question", status_code=202)
async def ask_question(request: QuestionRequest):
    """
    Submit content and a question for an LLM to answer through Redis streams.
    Returns a 202 Accepted response with the request ID for polling results.
    """
    api_logger.info(f"Question request received for model: {request.model}")
    try:
        # Add message to Redis question stream
        data = {
            "request_id": request.request_id,
            "content": request.content,
            "question": request.question,
            "model": request.model,
            "max_tokens": str(request.max_tokens),
            "temperature": str(request.temperature),
            "timestamp": str(time.time())
        }
        
        # Push to Redis stream
        redis_client.xadd(QUESTION_STREAM, data)
        api_logger.info(f"Question request {request.request_id} pushed to Redis stream")
        
        return {"request_id": request.request_id, "status": "processing"}
    except Exception as e:
        log_error(f"Failed to submit question request", e)
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")


@app.on_event("startup")
async def create_redis_streams():
    """Ensure all required Redis streams exist"""
    try:
        # Skip if Redis isn't available
        if redis_client is None:
            api_logger.warning("Redis not available - skipping stream creation")
            return
            
        # Create streams if they don't exist (add a dummy message that can be deleted later)
        for stream in [SUMMARY_STREAM, QUESTION_STREAM, RESULT_STREAM]:
            # Check if stream exists
            if not redis_client.exists(stream):
                api_logger.info(f"Creating Redis stream: {stream}")
                # Add a dummy message that will be processed and removed
                redis_client.xadd(stream, {"init": "init"}, maxlen=10)
        api_logger.info("All required Redis streams initialized")
    except Exception as e:
        log_error(f"Error initializing Redis streams", e)
        
@app.get("/get-llm-result/{request_id}")
async def get_llm_result(request_id: str):
    """
    Check if results for a given request ID are available.
    This endpoint polls Redis for results from LLM processing.
    """
    api_logger.info(f"Checking for results for request: {request_id}")
    try:
        # Check the in-memory cache first
        if request_id in llm_results:
            result = llm_results[request_id]
            api_logger.info(f"Result found in cache for request: {request_id}")
            return {"request_id": request_id, "status": "completed", **result}
        
        # If not in cache, query Redis stream for results
        # Get all messages from the result stream
        messages = redis_client.xread({RESULT_STREAM: '0'}, count=100)
        
        if not messages:
            api_logger.info(f"No results found yet for request: {request_id}")
            return {"request_id": request_id, "status": "processing"}
        
        # Find the result matching our request_id
        for stream_name, stream_messages in messages:
            for message_id, data in stream_messages:
                if data.get("request_id") == request_id:
                    api_logger.info(f"Result found in Redis for request: {request_id}")
                    
                    # If there was an error
                    if "error" in data:
                        return {
                            "request_id": request_id,
                            "status": "error",
                            "error": data["error"]
                        }
                    
                    # Parse the data properly
                    result_data = {}
                    for key, value in data.items():
                        if key != "request_id":  # We add this separately
                            # Handle usage data specially - convert from JSON string back to dict
                            if key == "usage" and value.startswith("{"):
                                try:
                                    result_data[key] = json.loads(value)
                                except json.JSONDecodeError:
                                    result_data[key] = value
                            else:
                                result_data[key] = value
                    
                    # Cache the result
                    llm_results[request_id] = result_data
                    
                    # Return the result
                    return {
                        "request_id": request_id, 
                        "status": "completed",
                        **result_data
                    }
        
        # No result found yet
        return {"request_id": request_id, "status": "processing"}
    except Exception as e:
        log_error(f"Error retrieving results for request: {request_id}", e)
        return {
            "request_id": request_id,
            "status": "error",
            "error": str(e)
        }

@app.get("/llm/models", response_model=LLMModelsResponse)
async def list_available_models():
    """
    Returns a list of available LLM models that can be used for summarization and Q&A
    """
    try:
        models = list(MODEL_CONFIGS.keys())
        api_logger.info(f"Retrieved {len(models)} available LLM models")
        return {"models": models}
    except Exception as e:
        log_error("Failed to retrieve available models", e)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve available models: {str(e)}")

@app.get("/llm/health")
async def check_llm_health():
    """
    Check if the LLM worker process is running and Redis streams are operational
    """
    try:
        # Check Redis connection
        redis_ping = redis_client.ping()
        
        # Check if worker streams exist
        summary_exists = redis_client.exists(SUMMARY_STREAM)
        question_exists = redis_client.exists(QUESTION_STREAM)
        result_exists = redis_client.exists(RESULT_STREAM)
        
        return {
            "redis_connected": bool(redis_ping),
            "streams": {
                "summary_stream": bool(summary_exists),
                "question_stream": bool(question_exists),
                "result_stream": bool(result_exists)
            },
            "status": "healthy" if redis_ping else "unhealthy"
        }
    except Exception as e:
        log_error("LLM health check failed", e)
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# ==================== TAX DOCUMENT PROCESSING ====================

# Import tax modules with graceful fallback for scipy/sklearn conflicts
try:
    from tax_document_parser import TaxDocumentParser
    from tax_calculation_engine import TaxCalculationEngine, FilingStatus
    from form_1040_generator import Form1040Generator
    TAX_MODULES_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Tax modules unavailable: {e}")
    print("[INFO] Tax document processing will use frontend-only approach")
    TAX_MODULES_AVAILABLE = False
    TaxDocumentParser = None
    TaxCalculationEngine = None
    FilingStatus = None
    Form1040Generator = None

from fastapi.responses import StreamingResponse

class PersonalInfo(BaseModel):
    first_name: str
    last_name: str
    ssn: str
    email: str
    filing_status: str
    tax_year: int
    dependents: Optional[List[Dict[str, str]]] = []

@app.post("/tax/upload")
async def upload_tax_documents(
    files: List[UploadFile] = File(...),
    first_name: str = "",
    last_name: str = "",
    ssn: str = "",
    email: str = "",
    filing_status: str = "",
    tax_year: int = 2024,
    background_tasks: BackgroundTasks = None
):
    """
    Upload and process tax documents (W-2, 1099-NEC, 1099-INT).
    Extracts structured data from tax forms.
    """
    api_logger.info(f"Tax document upload initiated. Files: {len(files)}, User: {first_name} {last_name}")
    
    temp_dir = None
    results = []
    validation_issues = []
    
    try:
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp(prefix="tax_docs_")
        api_logger.info(f"Created temp directory: {temp_dir}")
        
        # Initialize parser
        parser = TaxDocumentParser()
        
        # Process each uploaded file
        for file in files:
            # Validate file
            if not file.filename.lower().endswith('.pdf'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": "Only PDF files are supported"
                })
                continue
            
            # Check file size (5MB max)
            file_content = await file.read()
            file_size_mb = len(file_content) / (1024 * 1024)
            
            if file_size_mb > 5:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": f"File size {file_size_mb:.2f}MB exceeds 5MB limit"
                })
                continue
            
            # Save file to temp directory
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # Parse the document
            parse_result = parser.parse(file_path)
            parse_result["filename"] = file.filename
            
            # Add validation issues
            if parse_result.get("validation_issues"):
                validation_issues.extend(parse_result["validation_issues"])
            
            results.append(parse_result)
            api_logger.info(f"Processed file: {file.filename} - Type: {parse_result.get('document_type')}")
        
        # Calculate summary
        successful = sum(1 for r in results if r.get("status") == "success")
        failed = sum(1 for r in results if r.get("status") == "error")
        
        response = {
            "status": "success",
            "user": {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "filing_status": filing_status,
                "tax_year": tax_year
            },
            "summary": {
                "total_documents": len(files),
                "successful_documents": successful,
                "failed_documents": failed
            },
            "documents": results,
            "validation_issues": validation_issues,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save results to GCS if configured
        if GCS_BUCKET_NAME:
            try:
                result_key = f"tax_documents/{tax_year}/{first_name}_{last_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                blob = gcs_bucket.blob(result_key)
                blob.upload_from_string(json.dumps(response), content_type="application/json")
                response["gcs_location"] = result_key
                gcs_logger.info(f"Results saved to GCS: {result_key}")
            except Exception as e:
                gcs_logger.error(f"Failed to save results to GCS: {str(e)}")
        
        # Clean up temp directory in background
        if background_tasks:
            background_tasks.add_task(cleanup_temp_directory, temp_dir)
        
        return response
    
    except Exception as e:
        api_logger.error(f"Tax document upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
    finally:
        # Cleanup if no background task
        if temp_dir and not background_tasks:
            cleanup_temp_directory(temp_dir)

def cleanup_temp_directory(path: str):
    """Clean up temporary directory"""
    try:
        shutil.rmtree(path)
        api_logger.info(f"Cleaned up temp directory: {path}")
    except Exception as e:
        api_logger.error(f"Failed to cleanup temp directory {path}: {str(e)}")

@app.get("/tax/status/{upload_id}")
async def get_tax_document_status(upload_id: str):
    """
    Check the status of a tax document upload.
    Returns the extracted data and processing status.
    """
    try:
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis service unavailable")
        
        result = redis_client.get(f"tax_upload:{upload_id}")
        if not result:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        return json.loads(result)
    
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to get tax upload status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tax/calculate")
async def calculate_tax(
    upload_id: Optional[str] = None,
    filing_status: str = "Single",
    dependent_count: int = 0,
    w2_wages: float = 0.0,
    nec_income: float = 0.0,
    interest_income: float = 0.0,
    other_income: float = 0.0,
    federal_withheld_w2: float = 0.0,
    federal_withheld_1099: float = 0.0,
):
    """
    Calculate federal income tax liability based on extracted document data.
    Returns comprehensive tax calculation and refund/amount owed.
    """
    try:
        api_logger.info(f"Tax calculation initiated - Status: {filing_status}, Dependents: {dependent_count}")
        
        # Initialize calculation engine
        calc_engine = TaxCalculationEngine()
        
        # Prepare tax data
        tax_data = {
            "filing_status": filing_status,
            "dependent_count": dependent_count,
            "w2_wages": w2_wages,
            "nec_income": nec_income,
            "interest_income": interest_income,
            "other_income": other_income,
            "federal_withheld_w2": federal_withheld_w2,
            "federal_withheld_1099": federal_withheld_1099,
        }
        
        # Calculate tax
        result = calc_engine.process_tax_return(tax_data)
        
        if result.get("status") == "calculated":
            # Store in cache if Redis available
            if redis_client:
                calculation_id = str(uuid.uuid4())
                redis_client.setex(
                    f"tax_calculation:{calculation_id}",
                    3600,  # 1 hour expiry
                    json.dumps(result)
                )
                result["calculation_id"] = calculation_id
        
        return result
    
    except Exception as e:
        api_logger.error(f"Tax calculation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tax/generate-form-1040")
async def generate_form_1040(
    first_name: str,
    last_name: str,
    ssn: str,
    filing_status: str,
    tax_year: int = 2024,
    dependent_count: int = 0,
    w2_wages: float = 0.0,
    nec_income: float = 0.0,
    interest_income: float = 0.0,
    other_income: float = 0.0,
    federal_withheld_w2: float = 0.0,
    federal_withheld_1099: float = 0.0,
):
    """
    Generate a completed Form 1040 PDF based on tax data.
    """
    try:
        api_logger.info(f"Form 1040 generation initiated for {first_name} {last_name}")
        api_logger.info(f"Tax data: filing_status={filing_status}, w2_wages={w2_wages}, nec_income={nec_income}, int_income={interest_income}")
        
        # Calculate tax
        calc_engine = TaxCalculationEngine()
        tax_data = {
            "filing_status": filing_status,
            "dependent_count": dependent_count,
            "w2_wages": w2_wages,
            "nec_income": nec_income,
            "interest_income": interest_income,
            "other_income": other_income,
            "federal_withheld_w2": federal_withheld_w2,
            "federal_withheld_1099": federal_withheld_1099,
        }
        
        try:
            tax_calculation = calc_engine.process_tax_return(tax_data)
            api_logger.info(f"Tax calculation completed. Status: {tax_calculation.get('status')}")
        except Exception as calc_error:
            api_logger.error(f"Tax calculation error: {str(calc_error)}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Tax calculation failed: {str(calc_error)}")
        
        if tax_calculation.get("status") != "calculated":
            api_logger.error(f"Tax calculation status invalid: {tax_calculation.get('status')}")
            raise HTTPException(status_code=400, detail="Tax calculation failed")
        
        # Prepare taxpayer info
        taxpayer_info = {
            "first_name": first_name,
            "last_name": last_name,
            "ssn": ssn,
            "filing_status": filing_status,
            "tax_year": tax_year,
            "dependent_count": dependent_count,
        }
        
        # Generate Form 1040
        try:
            form_generator = Form1040Generator()
            pdf_buffer = form_generator.generate_form(taxpayer_info, tax_calculation)
            api_logger.info(f"Form 1040 generated successfully for {first_name} {last_name}")
        except Exception as form_error:
            api_logger.error(f"Form 1040 generation error: {str(form_error)}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Form generation failed: {str(form_error)}")
        
        # Save to GCS if configured
        if GCS_BUCKET_NAME:
            try:
                form_key = f"forms/1040/{tax_year}/{first_name}_{last_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                blob = gcs_bucket.blob(form_key)
                blob.upload_from_string(pdf_buffer.getvalue(), content_type="application/pdf")
                gcs_logger.info(f"Form 1040 saved to GCS: {form_key}")
            except Exception as e:
                gcs_logger.error(f"Failed to save Form 1040 to GCS: {str(e)}")
        
        return StreamingResponse(
            iter([pdf_buffer.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Form1040_{first_name}_{last_name}_{tax_year}.pdf"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Form 1040 generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tax/summary")
async def get_tax_summary():
    """
    Get summary statistics for all processed tax returns (if using Redis cache).
    """
    try:
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis service unavailable")
        
        # Get all calculation IDs
        keys = redis_client.keys("tax_calculation:*")
        total_calculations = len(keys)
        
        return {
            "status": "success",
            "total_tax_calculations": total_calculations,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to get tax summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))