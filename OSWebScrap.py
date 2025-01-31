from bs4 import BeautifulSoup
import requests
import os
import boto3
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()



# Initialize S3 client
session = boto3.Session(
    's3',
    aws_access_key_id=os.getenv('AWS_SERVER_PUBLIC_KEY'),
    aws_secret_access_key=os.getenv('AWS_SERVER_SECRET_KEY'),
    
)

s3 = session.client('s3')
bucket_name = os.getenv('AWS_BUCKET_NAME')
aws_region = os.getenv('AWS_REGION')

# List of disallowed file extensions
DISALLOWED_EXTENSIONS = [".pdf", ".xls", ".xlsx", ".doc", ".docx", ".ppt", ".pptx", ".zip", ".rar"]


def is_valid_url(url):
    """Check if the URL is valid and not pointing to a disallowed file type."""
    if not url.startswith(("http://", "https://")):
        print("Invalid URL. Please include http:// or https://.")
        return False

    if any(url.lower().endswith(ext) for ext in DISALLOWED_EXTENSIONS):
        print(f"URL points to a disallowed file type ({url.split('.')[-1]}).")
        return False

    return True


def upload_to_s3(file_content, s3_path, content_type="text/plain"):
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_path,
            Body=file_content,
            ContentType=content_type,
        )
        s3_url = f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{s3_path}"
        print(f"Uploaded to S3: {s3_url}")
        return s3_url
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None


def scrape_visual_data(url):
    """Scrape images and tables from the specified webpage and upload to S3."""
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Scrape and upload images
    img_tags = soup.find_all("img")
    images = []
    for idx, img_tag in enumerate(img_tags):
        img_url = img_tag.get("src")
        if not img_url:
            continue

        img_url = requests.compat.urljoin(url, img_url)

        try:
            img_data = requests.get(img_url).content
            s3_path = f"scraped_data/images/image_{idx + 1}.jpg"
            upload_url = upload_to_s3(img_data, s3_path, "image/jpeg")
            if upload_url:
                images.append(upload_url)
        except Exception as e:
            print(f"Failed to download image {img_url}: {e}")

    # Scrape and upload tables
    tables = []
    table_text = ""
    for table_idx, table in enumerate(soup.find_all("table"), start=1):
        table_data = []
        for row in table.find_all("tr"):
            row_data = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
            table_data.append(row_data)
        tables.append(table_data)

        # Convert table to string format
        table_text += f"Table {table_idx}:\n"
        for row in table_data:
            table_text += " | ".join(row) + "\n"
        table_text += "\n"

    # Upload table data to S3
    table_s3_path = "scraped_data/tables.txt"
    upload_to_s3(table_text.encode("utf-8"), table_s3_path, "text/plain")

    return {"images": images, "tables": tables, "tables_s3_url": table_s3_path}


def scrape_text_data_with_images(url):
    """Extract visible text and image references from the webpage and store Markdown on S3."""
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    # Extract all image references and format them for Markdown
    img_tags = soup.find_all("img")
    image_markdown = []
    for idx, img_tag in enumerate(img_tags):
        img_url = img_tag.get("src")
        alt_text = img_tag.get("alt", f"Image {idx + 1}")
        if img_url:
            img_url = requests.compat.urljoin(url, img_url)
            image_markdown.append(f"![{alt_text}]({img_url})")

    # Get visible text from the webpage
    text = soup.get_text()

    # Clean up and normalize whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    cleaned_text = "\n".join(chunk for chunk in chunks if chunk)

    # Append image references to the text content
    markdown_content = f"{cleaned_text}\n\n## Images\n\n" + "\n\n".join(image_markdown)

    # Upload to S3
    markdown_s3_path = "scraped_data/scraped_content.md"
    upload_to_s3(markdown_content.encode("utf-8"), markdown_s3_path, "text/markdown")

    return markdown_s3_path


def convert_to_markdown(data):
    """Convert scraped data into Markdown format and store on S3."""
    markdown_content = "# Extracted Web Content\n\n"

    # Add a section for images
    markdown_content += "## Images\n\n"
    for idx, image in enumerate(data["images"], start=1):
        markdown_content += f"![Image {idx}]({image})\n\n"

    # Add a section for tables
    markdown_content += "## Tables\n\n"
    for idx, table in enumerate(data["tables"], start=1):
        markdown_content += f"### Table {idx}\n\n"
        for row in table:
            markdown_content += "| " + " | ".join(row) + " |\n"
        markdown_content += "\n"

    # Upload Markdown to S3
    markdown_s3_path = "scraped_data/final_scraped_content.md"
    upload_to_s3(markdown_content.encode("utf-8"), markdown_s3_path, "text/markdown")
    return markdown_s3_path


if __name__ == "__main__":
    # Prompt user for a URL
    user_url = input("Enter the URL to scrape (must include http:// or https://): ").strip()

    if not is_valid_url(user_url):
        print("Exiting due to invalid URL.")
        exit(1)

    # Scrape text data
    markdown_s3_path = scrape_text_data_with_images(user_url)

    # Scrape visual data (images & tables)
    visual_data = scrape_visual_data(user_url)

    # Convert to final Markdown with images and tables
    final_markdown_s3_path = convert_to_markdown(visual_data)

    print(f"Scraped text Markdown uploaded: {markdown_s3_path}")
    print(f"Final Markdown with images & tables uploaded: {final_markdown_s3_path}")

