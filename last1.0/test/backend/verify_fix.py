with open(r'C:\Users\86187\Desktop\yuyi_pro_v2\webapp\static\js\app.js', 'r', encoding='utf-8') as f:
    content = f.read()

backtick = chr(96)  # backtick character
print(f"Total backticks: {content.count(backtick)}")
print(f"Has app.mount: {'app.mount' in content}")
print(f"Has app.use: {'app.use' in content}")

# Check template: ` pattern
import re
templates = re.findall(r'template:\s*' + backtick, content)
print(f"template: backtick found: {len(templates)} times")

# Show first few lines
lines = content.split('\n')
print(f"Total lines: {len(lines)}")
print(f"First line: {lines[0][:80]}")
print(f"Last line: {lines[-1][:80]}")

# Check for specific patterns
print(f"Has fetch with template: {'fetch(' + backtick in content}")
