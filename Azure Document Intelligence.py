import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from PIL import Image
from io import BytesIO
import base64

# Load environment variables from .env file
load_dotenv()

endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
key = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
form_url = os.getenv("SAMPLE_PDF_URL")

# Initialize Document Intelligence client
document_intelligence_client = DocumentIntelligenceClient(
    endpoint=endpoint, credential=AzureKeyCredential(key)
)

# Analyze the document
poller = document_intelligence_client.begin_analyze_document(
    "prebuilt-layout", AnalyzeDocumentRequest(url_source=form_url)
)
result = poller.result()

# Directory for storing markdown files and images
markdown_dir = "markdown_pages"
image_dir = os.path.join(markdown_dir, "images")
os.makedirs(markdown_dir, exist_ok=True)
os.makedirs(image_dir, exist_ok=True)

# Extract content for each page
for page_idx, page in enumerate(result.pages):
    page_number = page_idx + 1
    markdown_output = f"# Content from Page {page_number}\n\n"

    # Extract text lines
    markdown_output += "## Text Content\n"
    for line_idx, line in enumerate(page.lines):
        markdown_output += f"- Line {line_idx + 1}: {line.content}\n"

    # Extract tables
    if result.tables:
        markdown_output += "\n## Table Content\n"
        for table_idx, table in enumerate(result.tables):
            markdown_output += f"\n### Table {table_idx + 1}\n"
            markdown_output += f"**Rows:** {table.row_count}, **Columns:** {table.column_count}\n\n"
            markdown_output += "| Row | Column | Content |\n"
            markdown_output += "|-----|--------|---------|\n"
            for cell in table.cells:
                markdown_output += f"| {cell.row_index} | {cell.column_index} | {cell.content} |\n"

    # Extract images
    markdown_output += "\n## Images\n"
    if hasattr(page, "images") and page.images:
        for image_idx, image in enumerate(page.images):
            # Decode and save image
            image_data = BytesIO(base64.b64decode(image.content))
            img = Image.open(image_data)
            image_filename = f"page_{page_number}_image_{image_idx + 1}.png"
            image_path = os.path.join(image_dir, image_filename)
            img.save(image_path)

            # Add image reference to Markdown
            markdown_output += f"![Image {image_idx + 1}](images/{image_filename})\n"
    else:
        markdown_output += "No images found on this page.\n"

    # Save Markdown file for the current page
    markdown_file = os.path.join(markdown_dir, f"page_{page_number}.md")
    with open(markdown_file, "w", encoding="utf-8") as file:
        file.write(markdown_output)

print(f"Markdown files have been created for all pages in the directory: {markdown_dir}")
