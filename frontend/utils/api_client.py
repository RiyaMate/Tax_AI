import requests
import streamlit as st

# ----------------------------
# HEALTH CHECK
# ----------------------------
def check_fastapi_health():
    try:
        url = f"{st.session_state.fastapi_url}/health"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            st.session_state.api_connected = True
            return True
        return False
    except:
        st.session_state.api_connected = False
        return False

# ----------------------------
# UPLOAD PDF TO BACKEND
# ----------------------------
def upload_pdf(uploaded_file):
    try:
        url = f"{st.session_state.fastapi_url}/upload-pdf"
        files = {"file": (uploaded_file.name, uploaded_file.read(), "application/pdf")}
        r = requests.post(url, files=files)

        if r.status_code == 200:
            return r.json()
        return {"error": r.text}

    except Exception as e:
        return {"error": str(e)}

# ----------------------------
# REQUEST MARKDOWN CREATION
# ----------------------------
def convert_to_markdown(uploaded_file):
    try:
        url = f"{st.session_state.fastapi_url}/convert-pdf-to-markdown"
        files = {"file": (uploaded_file.name, uploaded_file.read(), "application/pdf")}
        r = requests.post(url, files=files)
        if r.status_code == 200:
            return r.json()
        return {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

# ----------------------------
# FETCH MARKDOWN FILES FROM GCS
# ----------------------------
def fetch_markdown_files():
    try:
        url = f"{st.session_state.fastapi_url}/fetch-latest-markdown-downloads"
        r = requests.get(url)

        if r.status_code == 200:
            return r.json().get("markdown_downloads", [])
        return []
    except:
        return []

# ----------------------------
# LLM SUMMARIZATION
# ----------------------------
def submit_summarization(content, model):
    try:
        url = f"{st.session_state.fastapi_url}/summarize"
        import uuid
        payload = {
            "request_id": str(uuid.uuid4()),
            "content": content,
            "model": model,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        r = requests.post(url, json=payload)

        if r.status_code == 200:
            result = r.json()
            st.session_state.summary_result = result

            # store history
            if st.session_state.selected_markdown_name:
                st.session_state.markdown_summaries[
                    st.session_state.selected_markdown_name
                ] = result

            return result
        return None
    except Exception as e:
        st.error(str(e))
        return None

# ----------------------------
# LLM QUESTION ANSWERING
# ----------------------------
def submit_question(content, question, model):
    try:
        url = f"{st.session_state.fastapi_url}/ask-question"
        import uuid
        payload = {
            "request_id": str(uuid.uuid4()),
            "content": content,
            "question": question,
            "model": model,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        r = requests.post(url, json=payload)

        if r.status_code == 200:
            result = r.json()
            st.session_state.question_result = result

            # save history
            if st.session_state.selected_markdown_name:
                st.session_state.markdown_qa[
                    st.session_state.selected_markdown_name
                ] = result

            return result
        return None
    except Exception as e:
        st.error(str(e))
        return None
