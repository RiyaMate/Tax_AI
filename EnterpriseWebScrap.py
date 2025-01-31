import os
import requests
import boto3
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_KEY = os.getenv('AWS_SERVER_PUBLIC_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SERVER_SECRET_KEY')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION')

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)

# Replace with your Apify API token
APIFY_TOKEN = os.getenv('APIFY_TOKEN')



# List of disallowed file extensions
DISALLOWED_EXTENSIONS = [".pdf", ".xls", ".xlsx", ".doc", ".docx", ".ppt", ".pptx", ".zip", ".rar"]

def is_valid_url(url):
    """Check if the URL is valid and not pointing to a disallowed file type."""
    if not url.startswith(("http://", "https://")):
        print("Invalid URL. Please include http:// or https://.")
        return False
    
    # Check for disallowed file extensions
    if any(url.lower().endswith(ext) for ext in DISALLOWED_EXTENSIONS):
        print(f"The URL points to a disallowed file type ({url.split('.')[-1]}).")
        return False
    
    return True

# Function to upload files to S3
def upload_to_s3(file_path, s3_key):
    try:
        s3_client.upload_file(file_path, AWS_BUCKET_NAME, s3_key)
        s3_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        print(f"Uploaded to S3: {s3_url}")
        return s3_url
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None

# Function to save images and upload to S3
def save_and_upload_images(image_urls):
    s3_image_urls = []
    
    for idx, url in enumerate(image_urls):
        try:
            response = requests.get(url)
            response.raise_for_status()
            file_name = f"image_{idx + 1}.jpg"
            
            with open(file_name, "wb") as f:
                f.write(response.content)
                
            # Upload to S3
            s3_url = upload_to_s3(file_name, f"scraped_data/images/{file_name}")
            if s3_url:
                s3_image_urls.append(s3_url)
                os.remove(file_name)  # Remove local file after upload
        except Exception as e:
            print(f"Failed to download image {url}: {e}")
    
    return s3_image_urls

# Function to generate markdown file and upload to S3
def generate_and_upload_markdown(text_content, image_urls):
    markdown_content = "# Extracted Webpage Data\n\n"
    markdown_content += "## Page Content\n\n" + text_content + "\n\n"
    
    if image_urls:
        markdown_content += "## Extracted Images\n\n"
        for idx, url in enumerate(image_urls):
            markdown_content += f"![Image {idx + 1}]({url})\n\n"
    
    md_filename = "extracted_content.md"
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    # Upload Markdown file to S3
    md_s3_url = upload_to_s3(md_filename, "scraped_data/extracted_content.md")
    os.remove(md_filename)  # Remove local file after upload
    
    return md_s3_url

# Main scraping function
if __name__ == "__main__":
    # Fetch Input from the user for a URL
    user_url = input("Enter the URL to scrape (must include http:// or https://): ").strip()
    # Validate URL input
    if not is_valid_url(user_url):
        exit(1)
    
    actor_id = "apify/puppeteer-scraper"
    input_data = {
        "startUrls": [{"url": user_url}],
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

    # Extract data using Apify
    client = ApifyClient(os.getenv('APIFY_TOKEN'))
    run = client.actor(actor_id).call(run_input=input_data)
    items = client.dataset(run["defaultDatasetId"]).list_items().items
    
    for item in items:
        images = item.get("images", [])
        text = item.get("text", "")
        
        # Upload images and markdown to S3
        s3_image_urls = save_and_upload_images(images)
        md_s3_url = generate_and_upload_markdown(text, s3_image_urls)
        
        print(f"Scraping and data upload complete. Markdown file stored at: {md_s3_url}")