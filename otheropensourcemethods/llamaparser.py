import os
from docling.parsers.pdf_parser import PDFParser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Example environment variable for credentials (if needed)
API_KEY = os.getenv("LLAMA_API_KEY")  # Replace with your own key name if applicable

def parse_pdf_to_markdown(pdf_path, output_dir):
    """
    Parses a PDF using docling, then converts each page's content into Markdown.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Parse the PDF using docling
    parser = PDFParser(pdf_path)
    pages = parser.get_pages()

    for page_number, page_content in enumerate(pages, start=1):
        # Extract the text content from the page
        text = page_content.get("text", "")

        # If text exists, write it to a Markdown file
        if text.strip():
            markdown_filename = os.path.join(output_dir, f"page_{page_number}.md")
            
            # Write to a Markdown file
            with open(markdown_filename, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Page {page_number} converted to {markdown_filename}")
        else:
            print(f"Page {page_number} has no content and was skipped.")

if __name__ == "__main__":
    # Input PDF file path
    pdf_file_path = "downloaded.pdf"  # Replace with the actual PDF file path

    # Output directory for Markdown files
    output_directory = "markdown_pages_output"

    # Parse and convert PDF to Markdown
    parse_pdf_to_markdown(pdf_file_path, output_directory)
