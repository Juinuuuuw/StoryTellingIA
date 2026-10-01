import re

path_idx = 'apresentacao/index.html'
with open(path_idx, 'r', encoding='utf-8') as f:
    idx_content = f.read()

def ic(name, extra_style=""):
    return f'<i data-lucide="{name}" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; {extra_style}"></i>'

def ic_color(color):
    return f'<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:{color}; fill:{color};"></i>'

idx_emojis = {
    # Jornada
    '👦': ic('user'),
    '👧': ic('user-round'),
    '🖥️': ic('monitor'),
    '🚀': ic('rocket'),

    # Hair length
    '💈': ic('scissors'),
    '✂️': ic('scissors'),
    '🌊': ic('waves'),
    '🎀': ic('gift'), # ponytail

    # Hair type
    '➖': ic('minus'),
    '〰️': ic('activity'),
    '🌀': ic('hurricane'),
    '🔘': ic('circle-dot'),

    # Hair/Skin/Eyes colors
    '⬛': ic_color('#2d3748'),
    '🟫': ic_color('#744210'),
    '🟡': ic_color('#ecc94b'),
    '🔴': ic_color('#e53e3e'),
    '🤍': ic_color('#fff5f5'),
    '🟤': ic_color('#975a16'),
    '🟨': ic_color('#fefcbf'),
    '🟢': ic_color('#48bb78'),
    '🔵': ic_color('#4299e1'),
    '⚫': ic_color('#1a202c'),

    # Quiz / End
    '🎬': ic('clapperboard'),
    '✔': ic('check'),
    '🏆': ic('award'),
    '👏': ic('thumbs-up'),
    '🎉': ic('party-popper'),
    '🧠': ic('brain'),
    '🔥': ic('flame'),
    '⭐': ic('star')
}

for e, icon_html in idx_emojis.items():
    idx_content = idx_content.replace(e, icon_html)

if 'lucide@latest' not in idx_content:
    idx_content = idx_content.replace('</body>', '  <script src="https://unpkg.com/lucide@latest"></script>\n  <script>lucide.createIcons();</script>\n</body>')

with open(path_idx, 'w', encoding='utf-8') as f:
    f.write(idx_content)
