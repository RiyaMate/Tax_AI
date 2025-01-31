import logging
import time
from pathlib import Path
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.base_models import FigureElement, InputFormat, Table
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
import boto3
import os

# AWS S3 Configuration
s3 = boto3.client('s3',
                  aws_access_key_id=os.getenv('AWS_SERVER_PUBLIC_KEY'),
                  aws_secret_access_key=os.getenv('AWS_SERVER_SECRET_KEY'))
bucket_name = os.getenv('AWS_BUCKET_NAME')

# Helper function to upload files to S3
def upload_file_to_s3(file_path, object_name):
    try:
        s3.upload_file(file_path, bucket_name, object_name)
        print(f"Uploaded {file_path} to s3://{bucket_name}/{object_name}")
    except Exception as e:
        print(f"Error uploading file {file_path}: {e}")


# Constants
IMAGE_RESOLUTION_SCALE = 2.0

def main():
    logging.basicConfig(level=logging.INFO)

    input_doc_path = Path("downloaded.pdf")
    output_dir = Path("output")

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

    # Save page images
    for page_no, page in conv_res.document.pages.items():
        page_image_filename = output_dir / f"{doc_filename}-{page_no}.png"
        with page_image_filename.open("wb") as fp:
            page.image.pil_image.save(fp, format="PNG")
        # Upload to S3
        upload_file_to_s3(str(page_image_filename), f"pdf_processing_pipeline/pdf_os_pipeline/markdown_outputs/{page_image_filename.name}")

    # Save images of figures and tables
    table_counter = 0
    picture_counter = 0
    for element, _level in conv_res.document.iterate_items():
        if isinstance(element, TableItem):
            table_counter += 1
            element_image_filename = output_dir / f"{doc_filename}-table-{table_counter}.png"
            with element_image_filename.open("wb") as fp:
                element.get_image(conv_res.document).save(fp, "PNG")
            # Upload to S3
            upload_file_to_s3(str(element_image_filename), f"pdf_processing_pipeline/pdf_os_pipeline/markdown_outputs/{element_image_filename.name}")

        if isinstance(element, PictureItem):
            picture_counter += 1
            element_image_filename = output_dir / f"{doc_filename}-picture-{picture_counter}.png"
            with element_image_filename.open("wb") as fp:
                element.get_image(conv_res.document).save(fp, "PNG")
            # Upload to S3
            upload_file_to_s3(str(element_image_filename), f"pdf_processing_pipeline/pdf_os_pipeline/markdown_outputs/{element_image_filename.name}")

    # Save markdown with embedded pictures
    md_filename_embedded = output_dir / f"{doc_filename}-with-images.md"
    conv_res.document.save_as_markdown(md_filename_embedded, image_mode=ImageRefMode.EMBEDDED)
    upload_file_to_s3(str(md_filename_embedded), f"pdf_processing_pipeline/pdf_os_pipeline/markdown_outputs/{md_filename_embedded.name}")

    # Save markdown with externally referenced pictures
    md_filename_referenced = output_dir / f"{doc_filename}-with-image-refs.md"
    conv_res.document.save_as_markdown(md_filename_referenced, image_mode=ImageRefMode.REFERENCED)
    upload_file_to_s3(str(md_filename_referenced), f"pdf_processing_pipeline/pdf_os_pipeline/markdown_outputs/{md_filename_referenced.name}")

    end_time = time.time() - start_time

    logging.info(f"Document converted and figures exported in {end_time:.2f} seconds.")


if __name__ == "__main__":
    main()
