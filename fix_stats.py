with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('payment_status, COUNT', 'payment_method, COUNT')
content = content.replace('GROUP BY payment_status', 'GROUP BY payment_method')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed payment_status -> payment_method")
