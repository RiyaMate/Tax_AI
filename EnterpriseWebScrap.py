import os
import requests
from apify_client import ApifyClient

# Replace with your Apify API token
APIFY_TOKEN = "InsertTokenHere"

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


def extract_webpage_data(actor_id, input_data):
    """Run an Apify actor to extract data."""
    # Initialize the Apify client
    client = ApifyClient(APIFY_TOKEN)

    # Run the actor
    run = client.actor(actor_id).call(run_input=input_data)

    # Retrieve the results
    dataset_id = run["defaultDatasetId"]
    items = client.dataset(dataset_id).list_items().items

    return items


def save_images(image_urls, output_folder):
    """Save images to the specified folder."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    saved_image_paths = []

    for img, url in enumerate(image_urls):
        try:
            response = requests.get(url)
            response.raise_for_status()
            image_path = os.path.join(output_folder, f"image_{img + 1}.jpg")
            with open(image_path, "wb") as f:
                f.write(response.content)
            print(f"Saved: {image_path}")
            saved_image_paths.append(image_path)
        except Exception as e:
            print(f"Failed to download image {url}: {e}")

    return saved_image_paths


def generate_markdown(text_content, image_urls, output_file):
    """Generate a Markdown file from text content and image references."""
    with open(output_file, "w", encoding="utf-8") as f:
        # Write the text content
        f.write("# Extracted Webpage Data\n\n")
        f.write("## Page Content\n\n")
        f.write(text_content + "\n\n")

        # Add image links
        if image_urls:
            f.write("## Extracted Images\n\n")
            for idx, url in enumerate(image_urls):
                f.write(f"![Image {idx + 1}]({url})\n\n")

    print(f"Markdown file created: {output_file}")


if __name__ == "__main__":
    # Fetch Input from the user for a URL
    user_url = input("Enter the URL to scrape (must include http:// or https://): ").strip()
    # Validate URL input
    if not is_valid_url(user_url):
        exit(1)

    # Actor ID for Apify Web Scraper
    actor_id = "apify/puppeteer-scraper"

    # Define scraper input using the provided URL
    input_data = {
        "startUrls": [{"url": user_url}],
        "maxConcurrency": 10,
        "maxPagesPerCrawl": 5,
        "pageFunction": """async ({ page, request }) => {
            try {
                await page.waitForSelector('img');

                const images = await page.$$eval('img', (imgs) =>
                    imgs.map((img) => img.src || img.getAttribute('ng-src'))
                );

                const validImages = [...new Set(images)].filter((url) => url && url.startsWith('http'));
                const textContent = await page.evaluate(() => document.body.innerText);

                return {
                    url: request.url,
                    title: await page.title(),
                    images: validImages,
                    text: textContent,
                };
            } catch (error) {
                return { url: request.url, error: error.message };
            }
        }""",
    }

    # Extract webpage data
    data = extract_webpage_data(actor_id, input_data)

    for item in data:
        images = item.get("images", [])
        text = item.get("text", "")

        # Save images to './downloaded_images' folder
        saved_image_urls = save_images(images, "./downloaded_images")

        # Generate Markdown
        markdown_filename = "extracted_content.md"
        generate_markdown(text, images, markdown_filename)

        print(f"Scraping and data extraction complete. Output saved to {markdown_filename}")