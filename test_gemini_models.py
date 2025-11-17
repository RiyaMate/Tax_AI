import os
from dotenv import load_dotenv
import requests

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    exit(1)

print(f"Using API Key: {gemini_api_key[:20]}...")
print("\nFetching available models...\n")

# List available models
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_api_key}"

try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    print("Available Models:")
    print("=" * 60)
    
    if "models" in data:
        for model in data["models"]:
            model_name = model.get("name", "unknown")
            display_name = model.get("displayName", "")
            print(f"[OK] {model_name} ({display_name})")
    else:
        print("No models found in response")
        print(f"Response: {data}")
        
except requests.exceptions.RequestException as e:
    print(f"ERROR: Failed to list models: {e}")
