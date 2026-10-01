import os

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

old_script = """  <script src="https://unpkg.com/lucide@latest"></script>
  <script>lucide.createIcons();</script>
</body>"""

files = ['apresentacao/index.html', 'apresentacao/dashboard.html', 'apresentacao/pre_questionario.html']

for p in files:
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace(old_script, '</body>')
    content = content.replace('</body>', observer_script)
    
    # Remove duplicate scripts just in case
    content = content.replace(observer_script + '\n' + observer_script, observer_script)
    
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)
