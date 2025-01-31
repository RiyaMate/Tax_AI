# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies required for Camelot & OpenCV
RUN apt-get update && apt-get install -y \
    ghostscript \
    poppler-utils \
    python3-tk \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    && apt-get clean

WORKDIR /app

COPY . .

# Install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --upgrade --prefer-binary --use-deprecated=legacy-resolver -r requirements.txt

EXPOSE 8080

# Start FastAPI with auto-reload for development
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
