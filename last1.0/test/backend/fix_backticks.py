import re

with open(r'C:\Users\86187\Desktop\yuyi_pro_v2\webapp\static\js\app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Count before
before_count = content.count('\\`')
print(f"Escaped backticks before: {before_count}")

# We need to be careful: \` inside template strings (the component templates) are valid escapes.
# But \` OUTSIDE template strings (in methods code) are wrong - they should be plain backticks.
#
# Strategy: The component template strings are: template: `...`
# Inside these, backticks would need escaping. But the escaped backticks we found are
# in fetch() calls and return statements OUTSIDE templates.
#
# Simple fix: replace \` with ` and \${ with ${ globally,
# because there are no intentional escaped backticks in this file.
# The template strings use ` delimiters, and inside them there are no literal backticks needed.

content = content.replace('\\`', '`')
content = content.replace('\\${', '${')

after_count = content.count('\\`')
print(f"Escaped backticks after: {after_count}")

with open(r'C:\Users\86187\Desktop\yuyi_pro_v2\webapp\static\js\app.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed!")
