#!/usr/bin/env python3
"""Fix unicode characters in landingai_utils.py for Windows compatibility"""

file_path = r'c:\Users\riyam\PDF_GREEN\LiteLLM_SummaryGenerator_with_Q-A\frontend\utils\landingai_utils.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace unicode characters
content = content.replace('[OK]', '[OK]')
content = content.replace('[NO]', '[NO]')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Fixed unicode characters in landingai_utils.py")
