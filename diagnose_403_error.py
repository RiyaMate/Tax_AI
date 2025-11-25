#!/usr/bin/env python3
"""
Diagnostic tool to identify and fix the 403 Forbidden error from LandingAI API
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_api_key():
    """Check if API key is properly configured"""
    print("\n" + "="*70)
    print("1️⃣  API KEY CHECK")
    print("="*70)
    
    api_key = os.getenv("VISION_AGENT_API_KEY")
    
    if not api_key:
        print("❌ VISION_AGENT_API_KEY is NOT set")
        print("   Solution: Add to .env file:")
        print("   VISION_AGENT_API_KEY=your_actual_key")
        return False
    
    print(f"✅ API key found")
    print(f"   Length: {len(api_key)} characters")
    print(f"   Starts with: {api_key[:20]}...")
    
    # Check for common issues
    if api_key.startswith("DUMMY") or api_key == "test":
        print("⚠️  WARNING: API key looks like a test/dummy key")
        return False
    
    if " " in api_key or "\n" in api_key:
        print("❌ ERROR: API key contains whitespace/newlines")
        print("   Solution: Clean up .env file")
        return False
    
    return True


def check_file_access():
    """Check if the PDF file exists and is readable"""
    print("\n" + "="*70)
    print("2️⃣  FILE ACCESS CHECK")
    print("="*70)
    
    pdf_file = Path("converted_image_2.pdf")
    
    if not pdf_file.exists():
        print(f"❌ File not found: {pdf_file.absolute()}")
        
        # List available files
        print("\n   Available PDF files in current directory:")
        pdfs = list(Path(".").glob("*.pdf"))
        if pdfs:
            for p in pdfs[:5]:
                print(f"   - {p.name}")
        else:
            print("   - No PDF files found")
        
        return False
    
    print(f"✅ File exists: {pdf_file.absolute()}")
    print(f"   Size: {pdf_file.stat().st_size:,} bytes")
    
    # Check if readable
    if not os.access(pdf_file, os.R_OK):
        print("❌ ERROR: File is not readable")
        print("   Solution: Check file permissions")
        return False
    
    print("✅ File is readable")
    
    # Check file size
    if pdf_file.stat().st_size == 0:
        print("❌ ERROR: File is empty (0 bytes)")
        return False
    
    if pdf_file.stat().st_size > 50 * 1024 * 1024:  # 50 MB
        print("⚠️  WARNING: File is very large (>50 MB)")
        print("   This may cause API timeouts")
        return True  # Not a hard error
    
    return True


def check_api_quota():
    """Check if API quota might be exceeded"""
    print("\n" + "="*70)
    print("3️⃣  API QUOTA CHECK")
    print("="*70)
    
    print("⚠️  Cannot check quota without API call")
    print("   Possible causes of 403 error:")
    print("   1. API quota exceeded for this month")
    print("   2. API key has insufficient permissions")
    print("   3. API key is for wrong environment")
    print("   4. IP address is blocked")
    print("   5. File format is not supported")
    
    return None


def check_network_access():
    """Check if we can reach the LandingAI API"""
    print("\n" + "="*70)
    print("4️⃣  NETWORK ACCESS CHECK")
    print("="*70)
    
    try:
        import requests
        
        print("Testing connection to LandingAI API...")
        response = requests.head(
            "https://api.va.landing.ai",
            timeout=5
        )
        print(f"✅ Can reach LandingAI API (status: {response.status_code})")
        return True
    
    except requests.exceptions.Timeout:
        print("❌ Connection timeout - network may be slow")
        return False
    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot reach LandingAI API - check internet connection")
        return False
    
    except Exception as e:
        print(f"⚠️  Unexpected error: {str(e)}")
        return None


def suggest_solutions():
    """Suggest solutions based on checks"""
    print("\n" + "="*70)
    print("💡 TROUBLESHOOTING GUIDE")
    print("="*70)
    
    api_key_ok = check_api_key()
    file_ok = check_file_access()
    network_ok = check_network_access()
    
    if not api_key_ok:
        print("\n🔧 Solution 1: Fix API Key")
        print("   a. Go to LandingAI dashboard: https://studio.landing.ai")
        print("   b. Get your actual API key")
        print("   c. Update .env file:")
        print("      VISION_AGENT_API_KEY=your_actual_key_here")
        print("   d. Restart the application")
    
    if not file_ok:
        print("\n🔧 Solution 2: Fix File Access")
        print("   a. Make sure converted_image_2.pdf exists in current directory")
        print("   b. Check file is not corrupted")
        print("   c. Ensure you have read permissions")
    
    if network_ok is False:
        print("\n🔧 Solution 3: Fix Network")
        print("   a. Check your internet connection")
        print("   b. Check if firewall is blocking LandingAI API")
        print("   c. Try again later if API is down")
    
    print("\n🔧 Solution 4: Try Alternative Extraction")
    print("   If you still get 403, try the fallback methods:")
    print("   - pdfplumber (for text-based PDFs)")
    print("   - pytesseract OCR (for scanned PDFs)")
    print("   - Gemini LLM extraction (for LLM processing)")
    
    print("\n🔧 Solution 5: Check LandingAI Status")
    print("   a. Visit: https://status.landing.ai")
    print("   b. Check if API is experiencing issues")
    print("   c. Check your account status/quota")


def main():
    """Run all diagnostic checks"""
    print("\n")
    print("🔍 LandingAI API 403 Error Diagnostic Tool")
    print("="*70)
    
    suggest_solutions()
    
    print("\n" + "="*70)
    print("Next Steps:")
    print("1. Follow the solutions above")
    print("2. Restart the application")
    print("3. Try processing the PDF again")
    print("="*70)
    print()


if __name__ == "__main__":
    main()
