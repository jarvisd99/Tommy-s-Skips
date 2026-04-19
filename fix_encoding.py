import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all nav-icon div contents
pattern = r'<div class="nav-icon">([^<]+)</div>'

def fix_nav_icon(match):
    val = match.group(1).strip()
    # Already clean
    if val in ['&#128203;', '&#10133;', '&#128209;', '&#128202;']:
        return match.group(0)
    # Return as-is for now, we'll fix by context
    return match.group(0)

# Get all matches with positions
fixes = []
for match in re.finditer(pattern, content):
    val = match.group(1).strip()
    if val in ['&#128203;', '&#10133;', '&#128209;', '&#128202;']:
        continue
    
    # Check what text follows to determine which icon
    after = content[match.end():match.end()+100]
    
    if 'Dashboard' in after:
        fixes.append((match.start(), match.end(), '<div class="nav-icon">&#128203;</div>'))
    elif 'New Order' in after:
        fixes.append((match.start(), match.end(), '<div class="nav-icon">&#10133;</div>'))
    elif 'All Orders' in after:
        fixes.append((match.start(), match.end(), '<div class="nav-icon">&#128209;</div>'))
    elif 'Stats' in after:
        fixes.append((match.start(), match.end(), '<div class="nav-icon">&#128202;</div>'))

# Apply fixes in reverse order to preserve positions
for start, end, replacement in reversed(fixes):
    content = content[:start] + replacement + content[end:]

# Also fix any garbled Add New Order button text
content = re.sub(r'>[^<]*Add New Order', '>&#10133; Add New Order', content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

icons = re.findall(pattern, content)
print('Nav icons after fix:')
for i in set(icons):
    print('  %s' % repr(i))

print('Fix complete!')
