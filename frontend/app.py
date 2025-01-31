"""import streamlit as st
import requests

# Page config
st.set_page_config(page_title="Lab3 Demo", page_icon="🔬")

# Get base URL from secrets
BASE_URL = st.secrets["BACKEND_URL"]

def call_root_endpoint():
    
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}

def call_health_endpoint():
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}

def call_env_demo_endpoint():
   
    try:
        response = requests.get(f"{BASE_URL}/env-demo")
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}

def upload_pdf(file):

    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        response = requests.post(f"{BASE_URL}/upload-pdf", files=files)
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}

# Main app
st.title("🔬 Lab3 Demo")
st.write("A simple demo showcasing FastAPI endpoints with environment variables")

# Create three columns
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Root Endpoint")
    if st.button("Call Root"):
        response = call_root_endpoint()
        st.json(response)

with col2:
    st.subheader("Health Check")
    if st.button("Check Health"):
        response = call_health_endpoint()
        st.json(response)

with col3:
    st.subheader("Env Demo")
    if st.button("Get Env Value"):
        response = call_env_demo_endpoint()
        st.json(response)

# File upload section
st.subheader("Upload a PDF File")
uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
if uploaded_file:
    st.write(f"File selected: {uploaded_file.name}")
    if st.button("Upload PDF"):
        response = upload_pdf(uploaded_file)
        st.json(response)
        st.rerun()

# Add some information about the configuration
st.markdown("---")
st.subheader("Configuration")
st.write(f"Backend URL: `{BASE_URL}`")
st.info("The backend URL is configured using .streamlit/secrets.toml")"""


import streamlit as st
import requests

# FastAPI Endpoint
FASTAPI_URL =  "http://127.0.0.1:8000/"

def scrape_url(url):
    """Sends the URL to FastAPI for scraping and returns the response."""
    payload = {"url": url}
    response = requests.post(FASTAPI_URL + "scrape/", json=payload)  # Fix here
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to scrape URL. Status code: {response.status_code}"}


def main():
    st.set_page_config(page_title="File and URL Upload", layout="wide")
    
    # Sidebar Navigation
    with st.sidebar:
        selected = st.radio("Main Menu", ["Home", "Upload", "Settings"])
        
        st.subheader("Upload File or Enter URL")
        
        # File Upload
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "docx", "csv"], key="file_uploader")
        
        # URL Input
        url_input = st.text_input("Enter URL", placeholder="https://example.com")
        
        # Dropdown for Enterprise or Open Source
        option = st.selectbox("Select Option", ["Enterprise", "Open Source"], index=0)
    
    st.title("Streamlit App with File Upload and URL Input")
    
    if selected == "Home":
        st.write("Welcome to the home page!")
    
    elif selected == "Upload":
        if uploaded_file is not None:
            st.success(f"File {uploaded_file.name} uploaded successfully!")
        
        if url_input and option == "Open Source":
            st.info("Scraping URL...")
            result = scrape_url(url_input)
            
            if "error" in result:
                st.error(result["error"])
            else:
                st.success("Scraping completed successfully!")
                st.write(f"Markdown S3 Path: {result['markdown_s3_path']}")
                st.write(f"Final Markdown S3 Path: {result['final_markdown_s3_path']}")
        
        st.write(f"Selected Option: {option}")
    
    elif selected == "Settings":
        st.write("Modify your application settings here.")

if __name__ == "__main__":
    main()

