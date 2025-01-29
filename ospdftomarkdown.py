import os
import pandas as pd
import boto3
from dotenv import load_dotenv
import io

# Load environment variables
load_dotenv()

# AWS S3 Configuration
session = boto3.Session(
    aws_access_key_id=os.getenv('AWS_SERVER_PUBLIC_KEY'),
    aws_secret_access_key=os.getenv('AWS_SERVER_SECRET_KEY'),
)

s3 = session.client('s3')
bucket_name = os.getenv('AWS_BUCKET_NAME')
output_s3_folder = "parsed_markdown"


def download_s3_file(bucket, key):
    """Download file from S3 and return its content."""
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj['Body'].read().decode('utf-8')


def create_markdown_from_s3(bucket, input_prefix, output_prefix):
    """Create markdown files from extracted PDF content stored in S3 and upload back to S3."""
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=input_prefix)
        files = response.get('Contents', [])
        
        pages = {}
        for file in files:
            filename = file['Key'].split('/')[-1]
            if filename.startswith("page_"):
                page_num = filename.split("_")[1].split(".")[0]  # Get page number
                if page_num not in pages:
                    pages[page_num] = {"text": [], "tables": [], "images": []}
                
                if filename.endswith("_text.txt"):
                    pages[page_num]["text"].append(file['Key'])
                elif filename.endswith(".csv"):
                    pages[page_num]["tables"].append(file['Key'])
                elif any(filename.endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
                    pages[page_num]["images"].append(file['Key'])
        
        for page_num, content in pages.items():
            markdown_content = f"# Page {page_num}\n\n"
            
            if content["text"]:
                markdown_content += "## Text Content\n\n"
                for text_file in content["text"]:
                    text_data = download_s3_file(bucket, text_file)
                    markdown_content += f"{text_data}\n\n"
            
            if content["tables"]:
                markdown_content += "## Tables\n\n"
                for table_file in content["tables"]:
                    table_data = download_s3_file(bucket, table_file)
                    df = pd.read_csv(io.StringIO(table_data))
                    markdown_content += f"### {table_file}\n\n"
                    markdown_content += df.to_markdown(index=False) + "\n\n"
            
            if content["images"]:
                markdown_content += "## Images\n\n"
                for image_file in content["images"]:
                    markdown_content += f"![{image_file}](s3://{bucket}/{image_file})\n\n"
            
            markdown_filename = f"page_{page_num}.md"
            markdown_key = f"{output_prefix}/{markdown_filename}"
            
            s3.put_object(Bucket=bucket, Key=markdown_key, Body=markdown_content.encode("utf-8"))
            print(f"Markdown file {markdown_filename} uploaded to S3://{bucket}/{markdown_key}")
        
    except Exception as e:
        print(f"Error creating markdown files: {e}")


if __name__ == "__main__":
    input_s3_folder = "output_data"
    create_markdown_from_s3(bucket_name, input_s3_folder, output_s3_folder)
