import re

path = 'apresentacao/pre_questionario.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

emojis = {
    '✨': 'sparkles'
}

for e, icon in emojis.items():
    svg = f'<i data-lucide="{icon}" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>'
    content = content.replace(e, svg)

if 'lucide@latest' not in content:
    content = content.replace('</body>', '  <script src="https://unpkg.com/lucide@latest"></script>\n  <script>lucide.createIcons();</script>\n</body>')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
