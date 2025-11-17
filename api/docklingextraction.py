import logging
import time
from pathlib import Path
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.base_models import FigureElement, InputFormat, Table
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from google.cloud import storage
import os
from open_source_parsing import upload_file_to_gcs

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

# For backwards compatibility - will use lazy versions when accessed
gcs_client = None
bucket = None

# Constants
IMAGE_RESOLUTION_SCALE = 2.0

def main(pdf_path,service_type):
    logging.basicConfig(level=logging.INFO)

    input_doc_path = Path(pdf_path)
    output_dir = Path(f"output/{Path(pdf_path).stem}")


    # Configure pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    start_time = time.time()
    # Convert the document
    conv_res = doc_converter.convert(input_doc_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    doc_filename = conv_res.input.file.stem
    # Define job-specific folder based on PDF filename and service type
    job_folder = f"{doc_filename}-{service_type}"
    gcs_folder = f"pdf_processing_pipeline/markdown_outputs/{job_folder}/"

    # Create a local output directory for the job
    output_dir = output_dir / job_folder
    output_dir.mkdir(parents=True, exist_ok=True)

    # [YES] Save page images inside the job-specific folder
    for page_no, page in conv_res.document.pages.items():
        page_image_filename = output_dir / f"{doc_filename}-{page_no}.png"
        with page_image_filename.open("wb") as fp:
            page.image.pil_image.save(fp, format="PNG")
        # [YES] Upload to GCS inside the job-specific folder
        upload_file_to_gcs(str(page_image_filename), f"{gcs_folder}{page_image_filename.name}")

    # [YES] Save images of tables and figures inside the job-specific folder
    table_counter = 0
    picture_counter = 0
    for element, _level in conv_res.document.iterate_items():
        if isinstance(element, TableItem):
            table_counter += 1
            element_image_filename = output_dir / f"{doc_filename}-table-{table_counter}.png"
            with element_image_filename.open("wb") as fp:
                element.get_image(conv_res.document).save(fp, "PNG")
            # [YES] Upload to GCS inside the job-specific folder
            upload_file_to_gcs(str(element_image_filename), f"{gcs_folder}{element_image_filename.name}")

        if isinstance(element, PictureItem):
            picture_counter += 1
            element_image_filename = output_dir / f"{doc_filename}-picture-{picture_counter}.png"
            with element_image_filename.open("wb") as fp:
                element.get_image(conv_res.document).save(fp, "PNG")
            # [YES] Upload to GCS inside the job-specific folder
            upload_file_to_gcs(str(element_image_filename), f"{gcs_folder}{element_image_filename.name}")

    # [YES] Save markdown with embedded images inside the job-specific folder
    md_filename_embedded = output_dir / f"{doc_filename}-with-images.md"
    conv_res.document.save_as_markdown(md_filename_embedded, image_mode=ImageRefMode.EMBEDDED)
    # [YES] Upload to GCS inside the job-specific folder
    upload_file_to_gcs(str(md_filename_embedded), f"{gcs_folder}{md_filename_embedded.name}")

    # [YES] Save markdown with externally referenced images inside the job-specific folder
    md_filename_referenced = output_dir / f"{doc_filename}-with-image-refs.md"
    conv_res.document.save_as_markdown(md_filename_referenced, image_mode=ImageRefMode.REFERENCED)
    # [YES] Upload to GCS inside the job-specific folder
    upload_file_to_gcs(str(md_filename_referenced), f"{gcs_folder}{md_filename_referenced.name}")

    end_time = time.time() - start_time
    logging.info(f"Document converted and saved in {end_time:.2f} seconds. Files stored in: {gcs_folder}")
