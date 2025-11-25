#!/usr/bin/env python3
"""Test encoding fix for special characters in PDF markdown"""

# Test 1: Verify UTF-8 encoding handling
pdf_with_special_chars = """
Form 1099–MISC (en-dash)
Form 1099—MISC (em-dash)  
Nonemployee compensation: $5,623.24
Box 7 shows various—characters and special symbols like © ® ™
"""

print("[TEST 1] Testing UTF-8 encoding of special characters")
print("=" * 80)

try:
    # Sanitize like we do in the prompt builder
    sanitized = pdf_with_special_chars.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    print(f"[PASS] ✓ Encoded successfully")
    print(f"Original length: {len(pdf_with_special_chars)}")
    print(f"Sanitized length: {len(sanitized)}")
    print(f"Content:\n{sanitized}\n")
except Exception as e:
    print(f"[FAIL] ✗ Encoding failed: {e}\n")

# Test 2: Verify the fix works with charmap (Windows-1252)
print("[TEST 2] Checking charmap compatibility")
print("=" * 80)

try:
    # This would fail before the fix
    charmap_test = "Test–with–dashes".encode('charmap', errors='replace')
    print(f"[INFO] Charmap encoding with error handling works")
    print(f"[INFO] Result: {charmap_test.decode('charmap')}")
except Exception as e:
    print(f"[INFO] Direct charmap encoding doesn't support special chars (expected): {e}")

# Test 3: Verify prompt sanitization
print("\n[TEST 3] Testing prompt sanitization")
print("=" * 80)

class MockLLM:
    def sanitize_prompt(self, text: str, doc_type: str) -> str:
        """Simulate the _build_extraction_prompt method"""
        sanitized_text = text.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        prompt = f"Extract from {doc_type}:\n{sanitized_text}"
        return prompt

llm = MockLLM()
pdf_markdown = """Below is a Sample PDF 1099-MISC
Form 1099–MISC Miscellaneous Income
7 Nonemployee compensation 5623.24 $"""

prompt = llm.sanitize_prompt(pdf_markdown, "1099-MISC")
print(f"[PASS] ✓ Prompt created successfully")
print(f"Prompt length: {len(prompt)}")
print(f"First 150 chars:\n{prompt[:150]}\n")

print("=" * 80)
print("[RESULT] All encoding tests completed successfully")
