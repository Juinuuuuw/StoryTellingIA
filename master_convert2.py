import re

def ic(name):
    # Use standard double quotes for attributes!
    return f'<i data-lucide="{name}" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>'

def ic_color(color):
    return f'<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:{color}; fill:{color};"></i>'

dash_emojis = {
    '&#128202;': ic('bar-chart-2'),
    '&#9193;': ic('skip-forward'),
    '&#11015;': ic('download'),
    '&#127919;': ic('target'),
    '&#128214;': ic('book-open'),
    '&#128221;': ic('edit'),
    '&#128101;': ic('users'),
    '&#128269;': ic('search'),
    '&#10005;': ic('x'),
    '&#128200;': ic('trending-up'),
    '&#127849;': ic('pie-chart'),
    '&#128308;': ic('circle-dot'),
    '&#128196;': ic('file-text'),
    '&#128338;': ic('clock'),
    '&#129335;': ic('help-circle'),
    '&#9989;': ic('check-circle'),
    '&#10060;': ic('x-circle'),
    '&#9888;': ic('alert-triangle'),
    '&#8594;': ic('arrow-right'),
    '&#127917;': ic('theater'),
    '&#9889;': ic('zap'),
    '&#127749;': ic('sunrise'),
    '&#8987;': ic('hourglass')
}

idx_emojis = {
    '👦': ic('user'),
    '👧': ic('user-round'),
    '🖥️': ic('monitor'),
    '🚀': ic('rocket'),
    '💈': ic('scissors'),
    '✂️': ic('scissors'),
    '🌊': ic('waves'),
    '🎀': ic('gift'),
    '➖': ic('minus'),
    '〰️': ic('activity'),
    '🌀': ic('hurricane'),
    '🔘': ic('circle-dot'),
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
    '🎬': ic('clapperboard'),
    '✔': ic('check'),
    '🏆': ic('award'),
    '👏': ic('thumbs-up'),
    '🎉': ic('party-popper'),
    '🧠': ic('brain'),
    '🔥': ic('flame'),
    '⭐': ic('star')
}

pre_emojis = {
    '✨': ic('sparkles')
}

observer_script = """
  <script src="https://unpkg.com/lucide@latest"></script>
  <script>
    if (window.lucide) {
      lucide.createIcons();
      const observer = new MutationObserver(() => {
        lucide.createIcons();
      });
      observer.observe(document.body, { childList: true, subtree: true });
    }
  </script>
</body>"""

# 1. PROCESS INDEX.HTML
with open('apresentacao/index.html', 'r', encoding='utf-8') as f:
    idx = f.read()

idx = idx.replace("emoji.innerText = o.emoji;", "emoji.innerHTML = o.emoji;")
idx = idx.replace("document.getElementById('quiz-fim-badge').innerText", "document.getElementById('quiz-fim-badge').innerHTML")
idx = idx.replace("document.getElementById('btn-personagem').innerText", "document.getElementById('btn-personagem').innerHTML")

# Replace outer single quotes with backticks for arrays
idx = re.sub(r"emoji:\s*'([^']+)'", r"emoji: `\1`", idx)
idx = idx.replace("'INICIAR JORNADA 🎬'", "`INICIAR JORNADA 🎬`")
idx = idx.replace("'CONFIRMAR ✔'", "`CONFIRMAR ✔`")

# Replace outer double quotes with backticks to allow inner double quotes from SVG tags!
idx = idx.replace('"Perfeito! 🏆"', '`Perfeito! 🏆`')
idx = idx.replace('"Muito bem! 👏"', '`Muito bem! 👏`')

for e, svg in idx_emojis.items():
    idx = idx.replace(e, svg)

idx = idx.replace('</body>', observer_script)
with open('apresentacao/index.html', 'w', encoding='utf-8') as f:
    f.write(idx)

# 2. PROCESS DASHBOARD.HTML
with open('apresentacao/dashboard.html', 'r', encoding='utf-8') as f:
    dash = f.read()

# Replace outer double quotes with backticks to allow inner double quotes
dash = dash.replace('"&#8987; Aguarde 5s..."', '`&#8987; Aguarde 5s...`')

for e, svg in dash_emojis.items():
    dash = dash.replace(e, svg)

dash = dash.replace('</body>', observer_script)
with open('apresentacao/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(dash)

# 3. PROCESS PRE_QUESTIONARIO.HTML
with open('apresentacao/pre_questionario.html', 'r', encoding='utf-8') as f:
    pre = f.read()

for e, svg in pre_emojis.items():
    pre = pre.replace(e, svg)

pre = pre.replace('</body>', observer_script)
with open('apresentacao/pre_questionario.html', 'w', encoding='utf-8') as f:
    f.write(pre)
