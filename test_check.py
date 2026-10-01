
import re
with open('servidor/quiz_manager.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'likert_cols = (\[.*?\])', text, re.DOTALL)
if m:
    likert_str = m.group(1)
    import ast
    likert_cols = ast.literal_eval(likert_str)
    pre_godspeed = [c.replace('Após a Interação', 'Antes da Interação') for c in likert_cols[16:39]]
    print(pre_godspeed[0])
    print(pre_godspeed[-1])
    print(len(pre_godspeed))

