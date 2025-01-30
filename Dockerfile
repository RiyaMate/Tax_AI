# Use an official Python runtime as a parent image
FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --upgrade --prefer-binary --use-deprecated=legacy-resolver -r requirements.txt

EXPOSE 8080

# Auto-reload FastAPI and run Streamlit
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload & streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0"]