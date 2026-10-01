import re

path = 'apresentacao/dashboard.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

emojis = {
    '&#128202;': 'bar-chart-2',
    '&#9193;': 'skip-forward',
    '&#11015;': 'download',
    '&#127919;': 'target',
    '&#128214;': 'book-open',
    '&#128221;': 'edit',
    '&#128101;': 'users',
    '&#128269;': 'search',
    '&#10005;': 'x',
    '&#128200;': 'trending-up',
    '&#127849;': 'pie-chart',
    '&#128308;': 'circle-dot',
    '&#128196;': 'file-text',
    '&#128338;': 'clock',
    '&#129335;': 'help-circle',
    '&#9989;': 'check-circle',
    '&#10060;': 'x-circle',
    '&#9888;': 'alert-triangle',
    '&#8594;': 'arrow-right'
}

for e, icon in emojis.items():
    svg = f'<i data-lucide="{icon}" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>'
    content = content.replace(e, svg)

if 'lucide@latest' not in content:
    content = content.replace('</body>', '  <script src="https://unpkg.com/lucide@latest"></script>\n  <script>lucide.createIcons();</script>\n</body>')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

path_idx = 'apresentacao/index.html'
with open(path_idx, 'r', encoding='utf-8') as f:
    idx_content = f.read()

idx_emojis = {
    '🎬': 'clapperboard',
    '✔': 'check',
    '🏆': 'award',
    '👏': 'thumbs-up',
    '🎉': 'party-popper',
    '🧠': 'brain',
    '🔥': 'flame',
    '⭐': 'star'
}

for e, icon in idx_emojis.items():
    svg = f'<i data-lucide="{icon}" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>'
    idx_content = idx_content.replace(e, svg)

if 'lucide@latest' not in idx_content:
    idx_content = idx_content.replace('</body>', '  <script src="https://unpkg.com/lucide@latest"></script>\n  <script>lucide.createIcons();</script>\n</body>')

with open(path_idx, 'w', encoding='utf-8') as f:
    f.write(idx_content)
