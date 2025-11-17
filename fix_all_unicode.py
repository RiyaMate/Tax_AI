#!/usr/bin/env python3
"""Fix ALL unicode characters in the project for Windows compatibility"""

import os
import glob

# Find all Python files
python_files = glob.glob(r'c:\Users\riyam\PDF_GREEN\LiteLLM_SummaryGenerator_with_Q-A/**/*.py', recursive=True)

unicode_chars = {
    '[OK]': '[OK]',
    '[NO]': '[NO]',
    '[YES]': '[YES]',
    '[FAIL]': '[FAIL]',
    '[WARN]': '[WARN]',
    '[TARGET]': '[TARGET]',
    '[CHART]': '[CHART]',
    '[MONEY]': '[MONEY]',
    '[SECURE]': '[SECURE]',
}

for file_path in python_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        for unicode_char, replacement in unicode_chars.items():
            content = content.replace(unicode_char, replacement)
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
    except Exception as e:
        pass

print("Done!")
