"""
Test IRS Chatbot with web scraping from irs.gov
"""

import requests
import json

API_ENDPOINT = "http://localhost:8000/api/tax/irs-chatbot"

test_questions = [
    "What are 2024 tax brackets?",
    "What is Form 1099-NEC used for?",
    "Tell me about self-employment tax",
    "What is the standard deduction?",
    "What forms do I need to file?",
    "How much tax do I owe?",  # Should trigger fallback
]

print("=" * 80)
print("IRS CHATBOT TEST - Web Scraping from irs.gov")
print("=" * 80)

for i, question in enumerate(test_questions, 1):
    print(f"\n[Test {i}] Question: {question}")
    print("-" * 80)
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json={"question": question},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Status: {result.get('status')}")
            print(f"📖 Title: {result.get('title')}")
            print(f"📍 Source: {result.get('source', 'Unknown')}")
            
            # Show answer (truncated)
            answer = result.get('answer', '')
            if len(answer) > 300:
                print(f"📝 Answer (first 300 chars):\n{answer[:300]}...")
            else:
                print(f"📝 Answer:\n{answer}")
            
            # Show available topics if no match
            if result.get('status') == 'no_match' and result.get('available_topics'):
                print(f"\n💡 Available Topics:")
                for topic in result['available_topics']:
                    print(f"   - {topic}")
        
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        print("   Make sure API is running: python -m uvicorn main:app --reload")

print("\n" + "=" * 80)
print("✅ IRS CHATBOT TEST COMPLETE")
print("=" * 80)
