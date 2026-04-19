"""Full encoding fix for Tommy's Skips app"""
import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count issues before fix
issues_before = 0
for ch in content:
    if ord(ch) > 127 and ord(ch) != 0xA3:  # Allow pound sign
        issues_before += 1

print("Non-ASCII chars before fix: %d" % issues_before)

# 1. Replace ALL non-ASCII characters in HTML template strings
# The pound sign should be &pound; in HTML
# Bullets should be | (pipe)
# Emojis should be removed or replaced with text

# Fix pound signs (various corrupted forms)
content = content.replace('\u00a3', '&pound;')
content = content.replace('\u00c2\u00a3', '&pound;')

# Fix bullets  
content = content.replace('\u2022', '|')
content = content.replace('&bull;', '|')

# Fix dashes
content = content.replace('\u2013', '-')
content = content.replace('\u2014', '-')

# Fix quotes
content = content.replace('\u2018', "'")
content = content.replace('\u2019', "'")
content = content.replace('\u201c', '"')
content = content.replace('\u201d', '"')

# Remove replacement characters
content = content.replace('\ufffd', '')

# Remove any remaining non-ASCII from HTML (but keep Python strings intact)
# We need to be careful here - only clean inside template strings

# Fix nav icons - replace with simple clean text
nav_replacements = [
    (r'<div class="nav-icon">[^<]*</div>\s*\n\s*Dashboard', '<div class="nav-icon">HOME</div>\n            Dashboard'),
    (r'<div class="nav-icon">[^<]*</div>\s*\n\s*New Order', '<div class="nav-icon">+ NEW</div>\n            New Order'),  
    (r'<div class="nav-icon">[^<]*</div>\s*\n\s*All Orders', '<div class="nav-icon">LIST</div>\n            All Orders'),
    (r'<div class="nav-icon">[^<]*</div>Stats', '<div class="nav-icon">STATS</div>\n            Stats'),
]

for pattern, replacement in nav_replacements:
    content = re.sub(pattern, replacement, content)

# Fix the Add Order button
content = re.sub(r'>[^<]*Add New Order<', '>+ Add New Order<', content)

# Fix nav-icon styling for text instead of emoji
old_nav_style = '.nav-icon { font-size: 0.85rem; font-weight: 700; color: inherit; letter-spacing: 0.5px; margin-bottom: 2px; }'
new_nav_style = '.nav-icon { font-size: 0.75rem; font-weight: 700; color: var(--orange); letter-spacing: 1px; margin-bottom: 4px; }'
content = content.replace(old_nav_style, new_nav_style)

# Also fix any other nav-icon styles
content = re.sub(
    r'\.nav-icon\s*\{[^}]*\}',
    '.nav-icon { font-size: 0.75rem; font-weight: 700; color: var(--orange); letter-spacing: 1px; margin-bottom: 4px; }',
    content
)

# Now scan for any remaining problematic characters
issues_after = 0
for i, ch in enumerate(content):
    if ord(ch) > 127:
        # Check if it's inside a Python string (not HTML)
        # Simple heuristic: if preceded by template markers, it's HTML
        issues_after += 1

print("Non-ASCII chars after fix: %d" % issues_after)

# Final: remove any truly garbled multi-byte sequences that aren't valid
# Replace sequences of non-ASCII followed by ASCII with just the ASCII
cleaned_lines = []
for line in content.split('\n'):
    # Only clean lines that are clearly HTML (inside template strings)
    new_line = ''
    for ch in line:
        if ord(ch) < 128 or ch in ['&']:
            new_line += ch
        elif ch == '\u00a3':
            new_line += '&pound;'
        else:
            # Skip non-ASCII in templates, keep in Python
            # Heuristic: if line has HTML tags, it's a template
            if '<' in line or 'class=' in line or 'style=' in line:
                pass  # Skip the char
            else:
                new_line += ch
    cleaned_lines.append(new_line)

content = '\n'.join(cleaned_lines)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
import py_compile
try:
    py_compile.compile('app.py', doraise=True)
    print("Compilation: OK")
except Exception as e:
    print("Compilation ERROR: %s" % str(e)[:100])

# Final check
with open('app.py', 'r', encoding='utf-8') as f:
    final = f.read()

remaining = sum(1 for ch in final if ord(ch) > 127)
print("Final non-ASCII count: %d" % remaining)
print("Full fix complete!")
