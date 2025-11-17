#!/usr/bin/env python
"""
FastAPI Server Startup Script
Runs the API server with Uvicorn
"""
import sys
import os

# Get the api directory path
api_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api')

# Change to api directory
os.chdir(api_dir)

# Add api directory to path
sys.path.insert(0, api_dir)

# Import and run main
if __name__ == "__main__":
    import uvicorn
    from main import app
    
    print("=" * 60)
    print("Starting FastAPI Server")
    print("=" * 60)
    print("API Documentation: http://localhost:8000/docs")
    print("Alternative Docs: http://localhost:8000/redoc")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
