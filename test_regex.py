import re

test = '| 1 | Wages, tips, other compensation | $23500.00 |'

# Test markdown table pattern
p_table = r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*\$?([\d,]+(?:\.\d+)?)\s*\|'
matches = list(re.finditer(p_table, test))
print(f'Table pattern matches: {len(matches)}')
if matches:
    for m in matches:
        print(f'  Box: {m.group(1)}, Label: {m.group(2)}, Value: {m.group(3)}')
else:
    print(f'  No matches in: {test}')
