"""Test extraction with actual ADE markdown table format"""
import sys
sys.path.insert(0, 'frontend/utils')

from universal_markdown_numeric_extractor import UniversalMarkdownNumericExtractor

# ADE markdown table format with pipes (actual format from LandingAI)
ade_markdown = '''
| **Box** | **Label** | **Value** |
| --- | --- | --- |
| 1 | Wages, tips, other compensation | $23500.00 |
| 2 | Federal income tax withheld | $1500.00 |
| 3 | Social Security wages | $23500.00 |
| 4 | Social Security tax withheld | $1457.00 |
| 5 | Medicare wages and tips | $23500.00 |
| 6 | Medicare tax withheld | $340.75 |
| 17 | State income tax | $800.00 |
'''

extractor = UniversalMarkdownNumericExtractor()
raw = extractor.extract_all_numeric_pairs(ade_markdown)

print('[DEBUG] Raw fields from ADE table format:')
for k, v in sorted(raw.items()):
    print(f'  {k}: {v}')
print(f'\nTotal: {len(raw)} fields')

print('\n[NORMALIZED] Tax fields:')
normalized = extractor.normalize_auto(raw)
for k, v in normalized.items():
    if v not in (0.0, None):
        print(f'  {k}: {v}')
