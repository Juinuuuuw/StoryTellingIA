import re

path = 'apresentacao/dashboard.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

emojis = {
    '&#127917;': 'theater',
    '&#9889;': 'zap',
    '&#127749;': 'sunrise',
    '&#8987;': 'hourglass',
    '🎭': 'theater',
    '⚡': 'zap',
    '🌅': 'sunrise',
    '⏳': 'hourglass'
}

for e, icon in emojis.items():
    svg = f'<i data-lucide="{icon}" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>'
    content = content.replace(e, svg)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
