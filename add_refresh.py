with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
new = old + '\n    <meta http-equiv="refresh" content="30">'

content = content.replace(old, new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

count = content.count('http-equiv="refresh"')
print("Auto-refresh added to %d pages" % count)
