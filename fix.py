import re

path = 'apresentacao/index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

def repl(m):
    return m.group(0).replace('"', "'")

content = re.sub(r'<i data-lucide=[^>]*></i>', repl, content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

script_match = re.search(r'<script>(.*?)</script>', content, flags=re.DOTALL)
if script_match:
    with open('temp_script.js', 'w', encoding='utf-8') as f:
        f.write(script_match.group(1))
