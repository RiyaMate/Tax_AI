import streamlit as st
import requests
import time

# Streamlit UI
st.set_page_config(page_title="PDF Processing App", layout="wide")
# Initialize session state variables if they do not exist
if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False
if "extraction_complete" not in st.session_state:
    st.session_state.extraction_complete = False
if "markdown_ready" not in st.session_state:
    st.session_state.markdown_ready = False
if "show_pdf_uploader" not in st.session_state:
    st.session_state.show_pdf_uploader = False
if "show_url_input" not in st.session_state:
    st.session_state.show_url_input = False


# FastAPI Base URL (Update this with the correct deployed FastAPI URL)
FASTAPI_URL = "http://localhost:8080"

# API Endpoints
UPLOAD_PDF_API = f"{FASTAPI_URL}/upload-pdf"
LATEST_FILE_API = f"{FASTAPI_URL}/get-latest-file-url"
PARSE_PDF_API = f"{FASTAPI_URL}/parse-pdf"
PARSE_PDF_AZURE_API = f"{FASTAPI_URL}/parse-pdf-azure"
CONVERT_MARKDOWN_API = f"{FASTAPI_URL}/convert-pdf-markdown"
FETCH_MARKDOWN_API = f"{FASTAPI_URL}/fetch-markdowns"
SCRAPE_OS_API = f"{FASTAPI_URL}/scrape"
SCRAPE_EN_API = f"{FASTAPI_URL}/enscrape"
FETCH_WEB_MARKDOWN_API = f"{FASTAPI_URL}/fetch-WebScrapMarkdowns"

st.title("📄 PDF Processing & Markdown Viewer")

with st.sidebar:
    # ✅ Select Service: PDF or Web URL
    st.subheader("Select Processing Type")
    processing_type = st.radio("Choose the processing method:", ["Select an option", "PDF Extraction", "Web URL Scraping"], index=0)

    selected = st.radio("Main Menu", ["Home", "Upload & Extract", "Settings"])

    # Initialize state variables to control visibility
    if "show_pdf_uploader" not in st.session_state:
        st.session_state.show_pdf_uploader = False
    if "show_url_input" not in st.session_state:
        st.session_state.show_url_input = False

    # Update visibility based on selection
    if processing_type == "PDF Extraction":
        st.session_state.show_pdf_uploader = True
        st.session_state.show_url_input = False
    elif processing_type == "Web URL Scraping":
        st.session_state.show_pdf_uploader = False
        st.session_state.show_url_input = True
    else:
        st.session_state.show_pdf_uploader = False
        st.session_state.show_url_input = False

    st.subheader("Upload File or Enter URL & Select Option")

    # Conditionally display file uploader or text input based on selection
    if st.session_state.show_pdf_uploader:
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"], key="file_uploader")

    if st.session_state.show_url_input:
        url_input = st.text_input("Enter URL", placeholder="https://example.com")

    # Dropdown for Enterprise or Open Source (Common for both)
    if processing_type in ["PDF Extraction", "Web URL Scraping"]:
        option = st.selectbox("Select Processing Option", ["", "Enterprise", "Open Source"], index=0)
# Function to Upload File to S3
def upload_pdf(file):
    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        response = requests.post(UPLOAD_PDF_API, files=files)
        if response.status_code == 200:
            st.session_state.file_uploaded = True
            return response.json()
        else:
            return {"error": f"Upload failed: {response.status_code}"}
    except requests.RequestException as e:
        return {"error": str(e)}

# Function to Trigger Open Source PDF Parsing (with Detailed Logging)
def process_open_source_pdf():
    with st.spinner("⏳ Processing Open Source PDF... Please wait."):
        progress_bar = st.progress(0)  # Initialize progress bar
        try:
            for i in range(10):  # Simulate progress while waiting
                time.sleep(1)
                progress_bar.progress((i + 1) * 10)  # Update progress

            # Step 1: Get Latest File URL
            response_latest = requests.get(LATEST_FILE_API)
            if response_latest.status_code != 200:
                progress_bar.empty()
                return {"error": f"❌ Failed to fetch latest file URL: {response_latest.text}"}

            # Step 2: Parse the PDF
            response_parse = requests.get(PARSE_PDF_API, timeout=600)  # Increased timeout
            if response_parse.status_code == 200:
                st.session_state.extraction_complete = True
                progress_bar.empty()
                return {"message": f"✅ Open Source PDF Analysis Completed! Click Markdown to view results.\n\n**Response:** {response_parse.text}"}
            else:
                progress_bar.empty()
                return {"error": f"❌ Parsing failed! Response: {response_parse.text}"}

        except requests.exceptions.RequestException as e:
            progress_bar.empty()
            return {"error": f"⚠️ API Request Failed: {str(e)}"}
# Function to Trigger Azure PDF Parsing (Enterprise) with Progress Bar & Debugging
def process_azure_pdf():
    with st.spinner("⏳ Processing PDF using Azure Document Intelligence... Please wait."):
        progress_bar = st.progress(0)

        try:
            for i in range(10):  # Simulate progress while waiting
                time.sleep(1)
                progress_bar.progress((i + 1) * 10)
             # Step 1: Get Latest File URL
            response_latest = requests.get(LATEST_FILE_API)
            if response_latest.status_code != 200:
                progress_bar.empty()
                return {"error": f"❌ Failed to fetch latest file URL: {response_latest.text}"}

            response = requests.get(PARSE_PDF_AZURE_API, timeout=600)  # Increased timeout

            if response.status_code == 200:
                st.session_state.extraction_complete = True
                progress_bar.empty()
                return {"message": f"✅ Azure-based PDF Analysis Completed! Click Markdown to view results.\n\n**Response:** {response.text}"}
            else:
                progress_bar.empty()
                return {"error": f"❌ Azure PDF Parsing failed! Response: {response.text}"}

        except requests.exceptions.RequestException as e:
            progress_bar.empty()
            return {"error": f"⚠️ API Request Failed: {str(e)}"}

# Function to Convert PDF to Markdown (With Progress Bar)
def convert_to_markdown():
    with st.spinner("⏳ Converting PDF to Markdown... Please wait."):
        progress_bar = st.progress(0)  # Initialize progress bar
        
        try:
            for i in range(8):  # Simulate progress
                time.sleep(1)  # Adjust as needed
                progress_bar.progress((i + 1) * 12)  # Update progress

            response = requests.get(CONVERT_MARKDOWN_API)

            if response.status_code == 200:
                st.session_state.markdown_ready = True
                progress_bar.empty()  # Remove progress bar
                return {"message": "✅ Markdown Conversion Completed! Click View to see results."}
            else:
                progress_bar.empty()
                return {"error": "❌ Markdown conversion failed!"}

        except requests.RequestException as e:
            progress_bar.empty()
            return {"error": str(e)}
# Function to Fetch Markdown File from S3
def fetch_markdown():
    try:
        response = requests.get(FETCH_MARKDOWN_API)
        if response.status_code == 200:
            markdown_files = response.json().get("files", [])
            if markdown_files:
                return {"markdown_file": markdown_files[-1]}  # Show the latest markdown file
            else:
                return {"error": "No markdown file found!"}
        else:
            return {"error": "Failed to fetch markdown files!"}
    except requests.RequestException as e:
        return {"error": str(e)}
# ✅ Function to Fetch Web Markdown
def fetch_web_markdown():
    try:
        response = requests.get(FETCH_WEB_MARKDOWN_API)
        if response.status_code == 200:
            markdown_files = response.json().get("files", [])
            if markdown_files:
                return {"markdown_file": markdown_files[-1]}
            else:
                return {"error": "No web markdown file found!"}
        else:
            return {"error": "Failed to fetch web markdown files!"}
    except requests.RequestException as e:
        return {"error": str(e)}

# ✅ Function to Scrape Open Source URL
def os_scrape_url(url):
    payload = {"url": url}
    response = requests.post(SCRAPE_OS_API, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to scrape URL. Status code: {response.status_code}"}

# ✅ Function to Scrape Enterprise URL
def en_scrape_url(url):
    payload = {"url": url}
    response = requests.post(SCRAPE_EN_API, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to scrape URL. Status code: {response.status_code}"}

# ✅ Main App Logic
if selected == "Upload & Extract":
    st.subheader("📤 Upload & Process Data")

    if uploaded_file and not st.session_state.file_uploaded:
        st.info("Uploading file to S3...")
        upload_response = upload_pdf(uploaded_file)
        if "error" in upload_response:
            st.error(upload_response["error"])
        else:
            st.success("✅ File Uploaded Successfully!")

    extract_btn = st.button("🛠 Extract")

    if extract_btn:
        if option == "":
            st.warning("⚠️ Please select 'Enterprise' or 'Open Source' before proceeding.")

        elif option == "Open Source" and st.session_state.file_uploaded:
            extract_response = process_open_source_pdf()
            if "error" in extract_response:
                st.error(extract_response["error"])
            else:
                st.success(extract_response["message"])

        elif option == "Enterprise" and st.session_state.file_uploaded:
            extract_response = process_azure_pdf()
            if "error" in extract_response:
                st.error(extract_response["error"])
            else:
                st.success(extract_response["message"])

    if st.session_state.extraction_complete:
        markdown_btn = st.button("📄 Convert to Markdown")
        if markdown_btn:
            markdown_response = convert_to_markdown()
            if "error" in markdown_response:
                st.error(markdown_response["error"])
            else:
                st.success(markdown_response["message"])

    if st.session_state.markdown_ready:
        view_btn = st.button("👀 View Markdown")
        if view_btn:
            markdown_file_response = fetch_markdown()
            if "error" in markdown_file_response:
                st.error(markdown_file_response["error"])
            else:
                markdown_file = markdown_file_response["markdown_file"]
                st.success(f"✅ Markdown File Ready: {markdown_file}")
                st.markdown(f"[Click to View Markdown](/{markdown_file})")

elif selected == "Settings":
    st.subheader("⚙️ Modify your application settings here.")