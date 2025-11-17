import os
import requests
from google.cloud import storage
import re
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Google Cloud Storage Configuration
gcp_project_id = os.getenv('GCP_PROJECT_ID')
gcs_bucket_name = os.getenv('GCS_BUCKET_NAME')

# Lazy initialization of GCS client
_gcs_client = None
_bucket = None

def get_gcs_client():
    """Get or initialize GCS client lazily."""
    global _gcs_client
    if _gcs_client is None:
        try:
            _gcs_client = storage.Client(project=gcp_project_id)
        except Exception as e:
            print(f"Warning: Could not initialize GCS client: {e}")
            print("GCS operations will not be available.")
            return None
    return _gcs_client

def get_bucket():
    """Get or initialize GCS bucket lazily."""
    global _bucket
    if _bucket is None:
        client = get_gcs_client()
        if client:
            _bucket = client.bucket(gcs_bucket_name)
    return _bucket

# For backwards compatibility
@property
def gcs_client():
    return get_gcs_client()

@property
def bucket():
    return get_bucket()

def check_file_exists_in_gcs(blob_name):
    """Check if a file exists in GCS."""
    try:
        b = get_bucket()
        if not b:
            return False
        blob = b.blob(blob_name)
        return blob.exists()
    except Exception as e:
        print(f"Error checking file existence: {e}")
        return False

def get_versioned_blob_name(base_blob_name):
    """Generate a versioned blob name for GCS."""
    # Extract base name and extension
    path = Path(base_blob_name)
    folder = str(path.parent)
    name = path.stem
    ext = path.suffix
    
    # Check if name already has a version suffix (v1, v2, etc.)
    version_match = re.search(r'_v(\d+)$', name)
    if version_match:
        # Extract current version number and base name
        current_version = int(version_match.group(1))
        base_name = name[:version_match.start()]
        new_version = current_version + 1
        new_name = f"{base_name}_v{new_version}"
    else:
        # No version suffix, add v1
        new_name = f"{name}_v1"
    
    # Create new blob name
    if folder and folder != '.':
        return f"{folder}/{new_name}{ext}"
    else:
        return f"{new_name}{ext}"

def upload_pdf_to_gcs(file_path, blob_name):
    """Upload a PDF to GCS with version control."""
    try:
        # Check if file exists in GCS
        if check_file_exists_in_gcs(blob_name):
            # Generate versioned blob name
            blob_name = get_versioned_blob_name(blob_name)
        
        # Upload file
        b = get_bucket()
        if not b:
            raise Exception("GCS bucket not available")
        blob = b.blob(blob_name)
        blob.upload_from_filename(file_path)
        return {
            "status": "success",
            "message": f"Uploaded {file_path} to gs://{gcs_bucket_name}/{blob_name}",
            "blob_name": blob_name
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error uploading file {file_path}: {e}",
            "blob_name": None
        }

def upload_file_to_gcs(file_path, blob_name):
    """Uploads a file to GCS."""
    try:
        b = get_bucket()
        if not b:
            raise Exception("GCS bucket not available")
        blob = b.blob(blob_name)
        blob.upload_from_filename(file_path)
        return f"Uploaded {file_path} to gs://{gcs_bucket_name}/{blob_name}"
    except Exception as e:
        return f"Error uploading file {file_path}: {e}"

def download_pdf(url, output_path):
    """Download PDF from a URL and save to local storage."""
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, "wb") as pdf_file:
            pdf_file.write(response.content)
        return f"PDF downloaded successfully: {output_path}"
    else:
        raise Exception(f"Failed to download PDF. Status code: {response.status_code}")

def upload_pdf_to_raw_input(file_path):
    """Upload PDF to the raw input folder in GCS with version control."""
    pdf_filename = os.path.basename(file_path)
    gcs_path = f"rawinput/{pdf_filename}"
    return upload_pdf_to_gcs(file_path, gcs_path)

