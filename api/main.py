from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from pydantic import BaseModel
import os
import sys
import boto3
import requests
from apify_client import ApifyClient
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import time
from Azure_Document_Intelligence import extract_and_upload_pdf
from EnterpriseWebScrap import is_valid_url, save_and_upload_images, generate_and_upload_markdown
from OSWebScrap import scrape_text_data_with_images, scrape_visual_data, convert_to_markdown
from open_source_parsing import extract_all_from_pdf
from docklingextraction import main


# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

#  Now import the parsing functions
#  Call the Docling conversion function
# Load environment variables from .env file
load_dotenv()

# AWS S3 Configuration
S3_BUCKET = os.getenv("AWS_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_SERVER_PUBLIC_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SERVER_SECRET_KEY")
AWS_REGION = "us-east-2"

# Apify Configuration
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Create FastAPI instance
app = FastAPI(
    title="Lab Demo API",
    description="Simple FastAPI application with health check and PDF upload to S3"
)

class ScrapeRequest(BaseModel):
    url: str


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for file details
latest_file_details = {}

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

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)) -> Dict[str, str]:
    """
    Uploads a PDF file to AWS S3 and returns the file URL, without storing locally.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no name")

    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET environment variable is missing")
    
    try:
        # Upload file directly to S3 (No Local Storage)
        s3_key = f"RawInputs/{file.filename}"
        s3_client.upload_fileobj(file.file, S3_BUCKET, s3_key)

        # Generate pre-signed URL
        file_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=3600  # 1 hour validity
        )

        # Save the file details globally
        global latest_file_details
        latest_file_details = {
            "filename": file.filename,
            "file_url": file_url,
            "s3_key": s3_key,
        }

        return {"filename": file.filename, "message": "PDF uploaded successfully!", "file_url": file_url}

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/get-latest-file-url")
async def get_latest_file_url() -> Dict[str, str]:
    """
    Retrieve the most recently uploaded file's URL, download it locally, and save the details.
    """
    if not latest_file_details:
        raise HTTPException(status_code=404, detail="No files have been uploaded yet")

    # Define local download path
    project_root = os.getcwd()
    downloaded_pdf_path = os.path.join(project_root, latest_file_details["filename"])

    # Download the file
    try:
        response = requests.get(latest_file_details["file_url"])
        response.raise_for_status()
        with open(downloaded_pdf_path, "wb") as pdf_file:
            pdf_file.write(response.content)
        print(f"[INFO] PDF downloaded successfully: {downloaded_pdf_path}")

        # Update the local path in the global file details
        latest_file_details["local_path"] = downloaded_pdf_path

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to download PDF: {str(e)}")

    return latest_file_details


@app.get("/parse-pdf")
async def parse_uploaded_pdf():
    """
    Uses the saved latest file details to extract content and upload results to S3.
    """
    try:
        # Check if the latest file details are available
        if not latest_file_details:
            raise HTTPException(status_code=404, detail="No file has been downloaded yet. Please fetch the latest file first.")

        # Extract the details from the saved data
        local_path = latest_file_details.get("local_path")
        filename = latest_file_details.get("filename")

        if not local_path or not filename:
            raise HTTPException(status_code=404, detail="Incomplete file details. Please fetch the latest file again.")

        # Define output directory for extraction
        output_dir = os.path.join(os.getcwd(), "output_data")

        # Extract data from the locally downloaded PDF
        extract_all_from_pdf(local_path, output_dir)

        return {
            "filename": filename,
            "message": "PDF parsed successfully and extracted data uploaded to S3",
            "local_path": local_path,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")

@app.get("/parse-pdf-azure")
async def parse_uploaded_pdf_azure():
    """
    Uses the saved latest file details to extract content using Azure Document Intelligence.
    """
    try:
        if not latest_file_details:
            raise HTTPException(status_code=404, detail="No file has been downloaded yet. Please fetch the latest file first.")

        local_path = latest_file_details.get("local_path")
        filename = latest_file_details.get("filename")

        if not local_path or not filename:
            raise HTTPException(status_code=404, detail="Incomplete file details. Please fetch the latest file again.")

        # Extract data from the locally downloaded PDF using Azure Document Intelligence
        extract_and_upload_pdf(local_path)

        return {
            "filename": filename,
            "message": "PDF parsed successfully using Azure Document Intelligence, data uploaded to S3",
            "local_path": local_path,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Azure PDF Processing failed: {str(e)}")
    
@app.get("/convert-pdf-markdown")
async def convert_pdf_to_markdown_api():
    """
    Uses the saved latest file details to convert the PDF into markdown using Docling.
    """
    try:
        if not latest_file_details:
            raise HTTPException(status_code=404, detail="No file has been downloaded yet. Please fetch the latest file first.")

        local_path = latest_file_details.get("local_path")
        filename = latest_file_details.get("filename")

        if not local_path or not filename:
            raise HTTPException(status_code=404, detail="Incomplete file details. Please fetch the latest file again.")

        
        main(local_path)


        return {
            "filename": filename,
            "message": "PDF successfully converted to Markdown using Docling and uploaded to S3",
            "local_path": local_path,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Docling Markdown conversion failed: {str(e)}")
    
@app.get("/fetch-markdowns")
async def fetch_markdowns_from_s3():
    """
    Fetch all Markdown files from the S3 markdown outputs folder and save them locally.
    """
    try:
        # Define S3 folder path where markdowns are stored
        s3_folder = "pdf_processing_pipeline/pdf_os_pipeline/markdown_outputs/"
        
        #  Check if the S3 folder exists
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=s3_folder)
        if response["KeyCount"] == 0:
            raise HTTPException(status_code=404, detail="Markdown folder not found in S3.")

        #  Check if any markdown files exist
        if "Contents" not in response:
            raise HTTPException(status_code=404, detail="No markdown files found in S3.")

        # Ensure the local directory for markdown files exists
        local_markdown_dir = "markdown_outputs"
        os.makedirs(local_markdown_dir, exist_ok=True)

        # Download only Markdown files
        downloaded_files = []
        for obj in response["Contents"]:
            file_key = obj["Key"]
            if file_key.endswith(".md"):  # ✅ Only process Markdown files
                local_file_path = os.path.join(local_markdown_dir, os.path.basename(file_key))
                
                # ✅ Download the file from S3
                s3_client.download_file(S3_BUCKET, file_key, local_file_path)
                downloaded_files.append(local_file_path)

        return {
            "message": f"Fetched {len(downloaded_files)} markdown files from S3.",
            "files": downloaded_files
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch markdown files: {str(e)}")
    

@app.post("/enscrape")
def scrape_webpage(request: ScrapeRequest):
    """Scrape a webpage using Apify and upload the results to S3."""
    if not is_valid_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid URL or unsupported file type.")
 
    # Apify actor configuration
    actor_id = "apify/puppeteer-scraper"
    input_data = {
        "startUrls": [{"url": request.url}],
        "maxConcurrency": 10,
        "maxPagesPerCrawl": 5,
        "pageFunction": """async ({ page, request }) => {
            try {
                await page.waitForSelector('img');
                const images = await page.$$eval('img', imgs => imgs.map(img => img.src || img.getAttribute('ng-src')));
                const validImages = [...new Set(images)].filter(url => url && url.startsWith('http'));
                const textContent = await page.evaluate(() => document.body.innerText);
                return { url: request.url, title: await page.title(), images: validImages, text: textContent };
            } catch (error) {
                return { url: request.url, error: error.message };
            }
        }""",
    }
 
    try:
        # Initialize Apify client
        client = ApifyClient(APIFY_TOKEN)
 
        # Run the Apify actor
        run = client.actor(actor_id).call(run_input=input_data)
 
        # Fetch the results
        dataset_id = run["defaultDatasetId"]
        items = client.dataset(dataset_id).list_items().items
 
        # Process the results
        for item in items:
            images = item.get("images", [])
            text = item.get("text", "")
            s3_image_urls = save_and_upload_images(images)
            md_s3_url = generate_and_upload_markdown(text, s3_image_urls)
            return {"markdown_s3_url": md_s3_url}
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    


@app.post("/OpenSourceWebscrape/")
async def scrape_url(scrape_request: ScrapeRequest):
    url = scrape_request.url
 
    if not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")
 
    # Scrape text data
    markdown_s3_path = scrape_text_data_with_images(url)
 
    # Scrape visual data (images & tables)
    visual_data = scrape_visual_data(url)
 
    # Convert to final Markdown with images and tables
    final_markdown_s3_path = convert_to_markdown(visual_data)
 
    return {
        "message": "Scraping completed successfully",
        "markdown_s3_path": markdown_s3_path,
        "final_markdown_s3_path": final_markdown_s3_path,
    }

@app.get("/fetch-WebScrapMarkdowns")
async def fetch_WebScrapMarkdowns_from_s3():
    """
    Fetch all Markdown files from the S3 markdown outputs folder and save them locally.
    """
    try:
        # Define S3 folder path where markdowns are stored
        s3_folder = "scraped_data/scraped_content.md"
       
        #  Check if the S3 folder exists
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=s3_folder)
        if response["KeyCount"] == 0:
            raise HTTPException(status_code=404, detail="Markdown not found in S3.")
 
        #  Check if any markdown files exist
        if "Contents" not in response:
            raise HTTPException(status_code=404, detail="No markdown files found in S3.")
 
        #  Ensure the local directory for markdown files exists
        local_markdown_dir = "markdown_outputs"
        os.makedirs(local_markdown_dir, exist_ok=True)
 
        #  Download only Markdown files
        downloaded_files = []
        for obj in response["Contents"]:
            file_key = obj["Key"]
            if file_key.endswith(".md"):  #  Only process Markdown files
                local_file_path = os.path.join(local_markdown_dir, os.path.basename(file_key))
               
                #  Download the file from S3
                s3_client.download_file(S3_BUCKET, file_key, local_file_path)
                downloaded_files.append(local_file_path)
 
        return {
            "message": f"Fetched {len(downloaded_files)} markdown files from S3.",
            "files": downloaded_files
        }
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch markdown files: {str(e)}")
