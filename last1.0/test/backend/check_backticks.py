with open(r'C:\Users\86187\Desktop\yuyi_pro_v2\webapp\static\js\app.js', 'rb') as f:
    data = f.read()

content = data.decode('utf-8')
lines = content.split('\n')

for i, line in enumerate(lines, 1):
    raw = line.encode('utf-8')
    # Find literal \` (backslash followed by backtick)
    idx = 0
    while True:
        pos = raw.find(b'\\`', idx)
        if pos == -1:
            break
        print(f"Line {i}: escaped backtick at col {pos}: {line.strip()[:120]}")
        idx = pos + 2
        break  # Only report first per line
