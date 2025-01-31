import os
import requests
import boto3
from apify_client import ApifyClient
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load environment variables
load_dotenv()


session = boto3.Session()
s3 = session.client('s3')
bucket_name = os.getenv('AWS_BUCKET_NAME')

#bucket_name=os.getenv('AWS_BUCKET_NAME')
region_name="us-east-2"


# Replace with your Apify API token
APIFY_TOKEN = os.getenv('APIFY_TOKEN')


if not APIFY_TOKEN:
    raise ValueError("Apify API token is missing. Please set the APIFY_TOKEN environment variable.")
 
# List of disallowed file extensions
DISALLOWED_EXTENSIONS = [".pdf", ".xls", ".xlsx", ".doc", ".docx", ".ppt", ".pptx", ".zip", ".rar"]
 
app = FastAPI()
 
class ScrapeRequest(BaseModel):
    url: str
 
def is_valid_url(url):
    """Check if the URL is valid and not pointing to a disallowed file type."""
    if not url.startswith(("http://", "https://")):
        return False
    if any(url.lower().endswith(ext) for ext in DISALLOWED_EXTENSIONS):
        return False
    return True
 
def upload_to_s3(file_path, s3_key):
    """Upload a file to S3 and return the S3 URL."""
    try:
        s3.upload_file(file_path, bucket_name, s3_key)
        return f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{s3_key}"
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None
 
def save_and_upload_images(image_urls):
    """Download images and upload them to S3."""
    s3_image_urls = []
    for idx, url in enumerate(image_urls):
        try:
            response = requests.get(url)
            response.raise_for_status()
            file_name = f"image_{idx + 1}.jpg"
            with open(file_name, "wb") as f:
                f.write(response.content)
            s3_url = upload_to_s3(file_name, f"scraped_data/images/{file_name}")
            if s3_url:
                s3_image_urls.append(s3_url)
            os.remove(file_name)
        except Exception as e:
            print(f"Failed to download or upload image {url}: {e}")
    return s3_image_urls
 
def generate_and_upload_markdown(text_content, image_urls):
    """Generate Markdown content and upload it to S3."""
    markdown_content = "# Extracted Webpage Data\n\n## Page Content\n\n" + text_content + "\n\n"
    if image_urls:
        markdown_content += "## Extracted Images\n\n"
        for idx, url in enumerate(image_urls):
            markdown_content += f"![Image {idx + 1}]({url})\n\n"
    md_filename = "extracted_content.md"
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    md_s3_url = upload_to_s3(md_filename, "scraped_data/extracted_content.md")
    os.remove(md_filename)
    return md_s3_url
 
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