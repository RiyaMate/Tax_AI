from bs4 import BeautifulSoup
import requests
import os

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

def scrape_visual_data(url, output_dir):
    """Scrape images, tables, and chart data from the specified webpage."""
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Scrape and save images
    img_tags = soup.find_all('img')
    images = []
    for idx, img_tag in enumerate(img_tags):
        img_url = img_tag.get('src')
        if not img_url:
            continue
        
        # Resolve relative URLs
        img_url = requests.compat.urljoin(url, img_url)

        try:
            img_data = requests.get(img_url).content
            img_filename = os.path.join(output_dir, f"image_{idx + 1}.jpg")
            with open(img_filename, 'wb') as img_file:
                img_file.write(img_data)
            print(f"Saved image: {img_filename}")
            images.append(img_filename)
        except Exception as e:
            print(f"Failed to download image {img_url}: {e}")

    # Scrape and save tables
    tables = []
    table_filename = os.path.join(output_dir, "tables.txt")
    with open(table_filename, 'w', encoding='utf-8') as table_file:
        for table_idx, table in enumerate(soup.find_all('table'), start=1):
            table_data = []
            for row in table.find_all('tr'):
                row_data = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                table_data.append(row_data)
            tables.append(table_data)

            # Write tables to file
            table_file.write(f"Table {table_idx}:\n")
            for row in table_data:
                table_file.write(" | ".join(row) + "\n")
            table_file.write("\n")

    print(f"Saved tables to {table_filename}")

    return {"images": images, "tables": tables}

def scrape_text_data_with_images(url):
    """Extract visible text and image references from the specified webpage."""
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful

    soup = BeautifulSoup(response.text, 'html.parser')

    # Remove script and style elements
    for script_or_style in soup(['script', 'style']):
        script_or_style.extract()

    # Extract all image references and format them for Markdown
    img_tags = soup.find_all('img')
    image_markdown = []
    for idx, img_tag in enumerate(img_tags):
        img_url = img_tag.get('src')
        alt_text = img_tag.get('alt', f"Image {idx + 1}")  # Use 'alt' if available
        if img_url:
            img_url = requests.compat.urljoin(url, img_url)
            image_markdown.append(f"![{alt_text}]({img_url})")

    # Get visible text from the webpage
    text = soup.get_text()

    # Clean up and normalize whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)

    # Append image references to the text content
    markdown_content = f"{cleaned_text}\n\n## Images\n\n" + "\n\n".join(image_markdown)

    return markdown_content

def convert_to_markdown(data, output_file):
    """Convert scraped data (text, images, tables) into Markdown format."""
    markdown_content = "# Extracted Web Content\n\n"

    # Add a section for images
    markdown_content += "## Images\n\n"
    for idx, image in enumerate(data['images'], start=1):
        relative_image_path = os.path.relpath(image)
        markdown_content += f"![Image {idx}]({relative_image_path})\n\n"

    # Add a section for tables
    markdown_content += "## Tables\n\n"
    for idx, table in enumerate(data['tables'], start=1):
        markdown_content += f"### Table {idx}\n\n"
        for row in table:
            markdown_content += "| " + " | ".join(row) + " |\n"
        markdown_content += "\n"

    # Save the Markdown file
    with open(output_file, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content)
    print(f"Markdown file saved: {output_file}")

if __name__ == "__main__":
    # Prompt user for a URL
    user_url = input("Enter the URL to scrape (must include http:// or https://): ").strip()

    if not is_valid_url(user_url):
        print("Exiting due to invalid URL.")
        exit(1)

    output_directory = "./scraped_content"

    # Scrape both visual and text data
    text_data = scrape_text_data_with_images(user_url)
    visual_data = scrape_visual_data(user_url, output_directory)

    # Save the Markdown content
    markdown_filename = os.path.join(output_directory, "scraped_content.md")
    os.makedirs(output_directory, exist_ok=True)
    
    with open(markdown_filename, "w", encoding="utf-8") as f:
        f.write(text_data)
        print(f"Markdown file created: {markdown_filename}")

    # Convert scraped content into Markdown
    convert_to_markdown(visual_data, markdown_filename)
