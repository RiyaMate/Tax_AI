import os
import fitz  # PyMuPDF
import camelot
import requests
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS S3 Configuration
session = boto3.Session(
    aws_access_key_id=os.getenv('AWS_SERVER_PUBLIC_KEY'),
    aws_secret_access_key=os.getenv('AWS_SERVER_SECRET_KEY'),
)

s3 = session.client('s3')
bucket_name = os.getenv('AWS_BUCKET_NAME')

def upload_file_to_s3(file_path, object_name):
    """Uploads a file to S3."""
    try:
        s3.upload_file(file_path, bucket_name, object_name)
        print(f"Uploaded {file_path} to s3://{bucket_name}/{object_name}")
    except Exception as e:
        print(f"Error uploading file {file_path}: {e}")

def download_pdf(url, output_path):
    """Download PDF from a URL and save to S3."""
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, "wb") as pdf_file:
            pdf_file.write(response.content)
        print(f"PDF downloaded successfully: {output_path}")
        upload_file_to_s3(output_path, "downloaded.pdf")
    else:
        raise Exception(f"Failed to download PDF. Status code: {response.status_code}")

def extract_text_from_pdf(file_path, output_folder):
    """Extract text from PDF and upload to S3."""
    with fitz.open(file_path) as pdf_document:
        for page_num in range(len(pdf_document)):
            text = pdf_document[page_num].get_text()
            text_filename = os.path.join(output_folder, f"page_{page_num + 1}_text.txt")
            with open(text_filename, "w", encoding="utf-8") as text_file:
                text_file.write(text)
            upload_file_to_s3(text_filename, f"output_data/page_{page_num + 1}_text.txt")

def extract_images_from_pdf(file_path, output_folder):
    """Extract images from PDF and upload to S3."""
    pdf_document = fitz.open(file_path)
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            if base_image is None or "image" not in base_image:
                continue
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = os.path.join(output_folder, f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}")
            with open(image_filename, "wb") as img_file:
                img_file.write(image_bytes)
            upload_file_to_s3(image_filename, f"output_data/{os.path.basename(image_filename)}")

def extract_tables_from_pdf(file_path, output_folder):
    """Extract tables from PDF and upload to S3."""
    tables = camelot.read_pdf(file_path, pages='all', flavor='stream')
    for table in tables:
        if table.parsing_report['accuracy'] >= 80:
            table_filename = os.path.join(output_folder, f"page_{table.page}_table.csv")
            table.to_csv(table_filename)
            upload_file_to_s3(table_filename, f"output_data/{os.path.basename(table_filename)}")

def extract_lists_from_pdf(file_path, output_folder):
    """Extract lists from PDF and upload to S3."""
    with fitz.open(file_path) as pdf_document:
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text = page.get_text()
            list_lines = [line.strip() for line in text.splitlines() if line.strip().startswith(('-', '*', '•', '○'))]
            if list_lines:
                list_filename = os.path.join(output_folder, f"page_{page_num + 1}_lists.txt")
                with open(list_filename, "w", encoding="utf-8") as list_file:
                    list_file.write("\n".join(list_lines))
                upload_file_to_s3(list_filename, f"output_data/{os.path.basename(list_filename)}")

def extract_all_from_pdf(file_path, output_folder):
    """Extract all data from a PDF and upload to S3."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    extract_text_from_pdf(file_path, output_folder)
    extract_images_from_pdf(file_path, output_folder)
    extract_tables_from_pdf(file_path, output_folder)
    extract_lists_from_pdf(file_path, output_folder)
    print("All extracted files uploaded to S3.")

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    downloaded_pdf_path = os.path.join(project_root, "downloaded.pdf")
    output_dir = os.path.join(project_root, "output_data")
    pdf_url = "https://arxiv.org/pdf/2408.09869"
    
    try:
        print("Downloading PDF...")
        download_pdf(pdf_url, downloaded_pdf_path)
        print("Extracting data from PDF...")
        extract_all_from_pdf(downloaded_pdf_path, output_dir)
    except Exception as e:
        print(f"Error: {e}")
