import streamlit as st
import requests
import time

# FastAPI Base URL (Update this with the correct deployed FastAPI URL)
FASTAPI_URL = "http://localhost:8080"

# API Endpoints
UPLOAD_PDF_API = f"{FASTAPI_URL}/upload-pdf"
LATEST_FILE_API = f"{FASTAPI_URL}/get-latest-file-url"
PARSE_PDF_API = f"{FASTAPI_URL}/parse-pdf"
PARSE_PDF_AZURE_API = f"{FASTAPI_URL}/parse-pdf-azure"
CONVERT_MARKDOWN_API = f"{FASTAPI_URL}/convert-pdf-markdown"
FETCH_MARKDOWN_API = f"{FASTAPI_URL}/fetch-markdowns"

# Streamlit UI
st.set_page_config(page_title="PDF Processing App", layout="wide")

st.title("📄 PDF Processing & Markdown Viewer")

# Sidebar Navigation
with st.sidebar:
    selected = st.radio("Main Menu", ["Home", "Upload & Extract", "Settings"])

    st.subheader("Upload File & Select Option")

    # File Upload
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"], key="file_uploader")

    # Dropdown for Enterprise or Open Source
    option = st.selectbox("Select Processing Option", ["", "Enterprise", "Open Source"], index=0)

# Initialize session state
if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False
if "extraction_complete" not in st.session_state:
    st.session_state.extraction_complete = False
if "markdown_ready" not in st.session_state:
    st.session_state.markdown_ready = False

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
if selected == "Upload & Extract":
    st.subheader("📤 Upload & Process PDF")

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
        st.info("Processing Open Source PDF...")
        extract_response = process_open_source_pdf()
        if "error" in extract_response:
            st.error(extract_response["error"])  # Display detailed API error
        else:
            st.success(extract_response["message"])

    elif option == "Enterprise" and st.session_state.file_uploaded:
        st.info("Processing PDF using Azure Document Intelligence...")
        extract_response = process_azure_pdf()
        if "error" in extract_response:
            st.error(extract_response["error"])  # Display detailed API error
        else:
            st.success(extract_response["message"])

# Markdown Button (Appears only after Extraction is Done)
if st.session_state.extraction_complete:
    markdown_btn = st.button("📄 Convert to Markdown")

    if markdown_btn:
        markdown_response = convert_to_markdown()
        if "error" in markdown_response:
            st.error(markdown_response["error"])
        else:
            st.success(markdown_response["message"])

# View Button (Appears only after Markdown is Ready)
if st.session_state.markdown_ready:
    view_btn = st.button("👀 View Markdown")

    if view_btn:
        st.info("Fetching latest Markdown file...")
        markdown_file_response = fetch_markdown()
        if "error" in markdown_file_response:
            st.error(markdown_file_response["error"])
        else:
            markdown_file = markdown_file_response["markdown_file"]
            st.success(f"✅ Markdown File Ready: {markdown_file}")
            st.markdown(f"[Click to View Markdown](/{markdown_file})")

elif selected == "Settings":
    st.subheader("⚙️ Modify your application settings here.")
