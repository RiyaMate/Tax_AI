import streamlit as st
import requests
 
# FastAPI Endpoint
FASTAPI_URL =  "http://127.0.0.1:8000/"
 
def en_scrape_url(url):
    """Sends the URL to FastAPI for scraping and returns the response."""
    payload = {"url": url}
    response = requests.post(FASTAPI_URL + "enscrape/", json=payload)  # Fix here
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to scrape URL. Status code: {response.status_code}"}
    
def os_scrape_url(url):
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
            result = os_scrape_url(url_input)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success("Scraping completed successfully!")
                st.write(f"Markdown S3 Path: {result['markdown_s3_path']}")
                st.write(f"Final Markdown S3 Path: {result['final_markdown_s3_path']}")
        if url_input and option == "Enterprise":
            st.info("Scraping URL...")
            result = en_scrape_url(url_input)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success("Scraping completed successfully!")
                st.write(f"Markdown S3 Path: {result['markdown_s3_url']}")
                #st.write(f"Final Markdown S3 Path: {result['final_markdown_s3_path']}")
        st.write(f"Selected Option: {option}")
    elif selected == "Settings":
        st.write("Modify your application settings here.")
 
if __name__ == "__main__":
    main()