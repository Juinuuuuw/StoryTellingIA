from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import ollama
from datetime import datetime
import os
import re
import json
import threading
import time
from state_manager import manager
import rag_historico
import canonical_scenes
import quiz_manager

quiz_manager.init_db()

app = Flask(__name__)
CORS(app) # Habilita CORS para todas as rotas

MODELO = 'phi4-mini'  # 3.8B — muito mais rápido que llama3.1 para JSON estruturado; cabe em 6 GB VRAM

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAIZ_PROJETO = os.path.join(BASE_DIR, "..")
PASTA_HISTORIAS = os.path.join(RAIZ_PROJETO, "historias")
PASTA_GERADAS = os.path.join(RAIZ_PROJETO, "historias_geradas")
PASTA_APRESENTACAO = os.path.join(RAIZ_PROJETO, "apresentacao")

os.makedirs(PASTA_HISTORIAS, exist_ok=True)
os.makedirs(PASTA_GERADAS, exist_ok=True)

# ============================================================
# ROTAS DE ARQUIVOS ESTÁTICOS
# ============================================================

@app.route('/apresentacao/')
def serve_apresentacao_index():
    diretorio = os.path.abspath(os.path.join(BASE_DIR, "..", "apresentacao"))
    return send_from_directory(diretorio, "index.html")

@app.route('/apresentacao/<path:filename>')
def serve_apresentacao_files(filename):
    diretorio = os.path.abspath(os.path.join(BASE_DIR, "..", "apresentacao"))
    return send_from_directory(diretorio, filename)

@app.route('/images/<path:filename>')
def serve_image(filename):
    diretorio = os.path.abspath(os.path.join(BASE_DIR, "..", "historias_geradas"))
    safe_filename = filename.replace("\\", "/")
    return send_from_directory(diretorio, safe_filename)

@app.route('/check_image/<path:filename>')
def check_image(filename):
    diretorio = os.path.abspath(os.path.join(BASE_DIR, "..", "historias_geradas"))
    safe_filename = filename.replace("/", os.sep).replace("\\", os.sep)
    if os.path.exists(os.path.join(diretorio, safe_filename)):
        return jsonify({"ready": True})
    return jsonify({"ready": False})

# ============================================================
# CONFIGURAÇÃO DE ESTILO (Estilo Anime 2D)
# ============================================================
ESTILO_TOONYOU = "masterpiece, best quality, highres, anime style, 2d illustration, studio ghibli style, vibrant vivid colors, highly detailed, cel shading"

# Negative base — usado em quadros COM 1 personagem
_NEGATIVE_BASE = "3d, cgi, render, 2.5d, photorealistic, realistic, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, dragon, monster, creature, beast, demon, fantasy creature, mythical creature, dinosaur, reptile creature, serpent, wyvern, lizard creature, alien, robot animal, mechanical beast"
_NEGATIVE_MULTI = "(2 people:1.5), (two people:1.5), (multiple people:1.5), (two characters:1.5), (duo:1.4), (group:1.4), (3 people, 4 people, crowd:1.4), merged faces, merged bodies, fused characters, extra person, duplicate character, extra face, extra head"

NEGATIVE_TOONYOU     = f"{_NEGATIVE_BASE}, {_NEGATIVE_MULTI}"
NEGATIVE_CHAR_ISOLADO = f"{_NEGATIVE_BASE}, {_NEGATIVE_MULTI}, background scenery, detailed background, complex background, gradient background"

# Negative para quadros de cenário PURO — bloqueia qualquer pessoa
NEGATIVE_CENA_PURA = f"{_NEGATIVE_BASE}, people, person, character, human, man, woman, child, boy, girl, figure, silhouette, face, body, hands, (any human:1.5)"

# Prompts específicos para fundo sem personagens (isolamento rembg)
ESTILO_FUNDO    = "masterpiece, best quality, highres, anime style, 2d illustration, studio ghibli style, vibrant vivid colors, highly detailed scenery, cel shading, empty scene, background art, environmental concept art, cinematic wide shot"
NEGATIVE_FUNDO  = NEGATIVE_CENA_PURA


def _acao_para_keywords(acao: str, student_name: str, npc_name: str) -> str:
    """
    Converte uma frase de ação narrativa em keywords visuais compactas para o gerador de imagens.
    Remove referências a personagens pelo nome (o gerador não entende "Mario observes X").
    Exemplos:
      "Mario observes the Bombe rotors" → "observing, focused gaze, mechanical rotors"
      "Alan Turing explains the Universal Machine" → "explaining, gesturing, chalkboard with equations"
    """
    import re
    # Remove o nome dos personagens da ação (case-insensitive)
    for nome in [student_name, npc_name]:
        if nome:
            acao = re.sub(re.escape(nome), '', acao, flags=re.IGNORECASE)

    # Limpa artigos e preposições iniciais comuns + espaços duplicados
    acao = re.sub(r'\b(the|a|an|of|with|and|to|at|in|on|by|for|from|while)\b', ' ', acao, flags=re.IGNORECASE)
    acao = re.sub(r'\s{2,}', ' ', acao).strip(' ,')

    # Converte para gerúndio-like keywords: "adjusts rotors" → "adjusting rotors"
    # Substitui verbos simples no presente pelo gerúndio onde possível
    verb_map = {
        r'\badjusts?\b': 'adjusting', r'\bexplains?\b': 'explaining',
        r'\bobserves?\b': 'observing', r'\blooks?\b': 'looking intently',
        r'\bworks?\b': 'working', r'\bexamines?\b': 'examining closely',
        r'\bsmiles?\b': 'smiling', r'\bpoints?\b': 'pointing',
        r'\bwrites?\b': 'writing', r'\breads?\b': 'reading',
        r'\bstands?\b': 'standing', r'\bsits?\b': 'sitting',
        r'\bholds?\b': 'holding', r'\breaches?\b': 'reaching',
        r'\bturns?\b': 'turning', r'\bpushes?\b': 'pushing',
        r'\bpulls?\b': 'pulling', r'\bpoints?\b': 'pointing',
        r'\blistens?\b': 'listening attentively', r'\bthinks?\b': 'thinking, hand on chin',
        r'\bgestures?\b': 'gesturing expressively',
    }
    for pattern, replacement in verb_map.items():
        acao = re.sub(pattern, replacement, acao, flags=re.IGNORECASE)

    # Trunca para evitar prompts gigantes
    tokens = acao.split()
    if len(tokens) > 10:
        tokens = tokens[:10]
    result = ' '.join(tokens).strip(' ,')
    return result if result else 'standing, neutral pose'


# ============================================================
# VISUAL DO PERSONAGEM — gênero e tom de pele estáveis
# ============================================================
# O ToonYou foi treinado com tags estilo Danbooru: "1boy"/"1girl" e "dark skin" são
# tags fortes; "1man"/"1woman"/"ebony complexion" quase não pesam e o modelo cai no
# padrão (menina de pele clara). Por isso trocamos a tag de gênero da descrição pela
# tag forte e reforçamos o negative com o gênero/pele opostos.
_TAG_GENERO_INICIAL = re.compile(r'^\s*(?:solo\s*,\s*)?1(?:man|woman|boy|girl|person|child)\b\s*,?\s*', re.IGNORECASE)
_PELE_ESCURA = re.compile(r'dark[- ](?:brown )?skin|dark-skinned|ebony|african|\bblack (?:man|woman|person)\b', re.IGNORECASE)


def genero_do_visual(desc, padrao="Masculino"):
    """Deduz o gênero de uma descrição visual ('1man, ...' / '1woman, ...')."""
    d = (desc or "").lower()
    if re.match(r'\s*(?:solo\s*,\s*)?1(?:woman|girl)\b', d):
        return "Feminino"
    if re.match(r'\s*(?:solo\s*,\s*)?1(?:man|boy)\b', d):
        return "Masculino"
    if re.search(r'\b(?:woman|female|girl|lady)\b', d):
        return "Feminino"
    if re.search(r'\b(?:man|male|boy)\b', d):
        return "Masculino"
    return padrao


def montar_visual_personagem(desc, genero):
    """
    Retorna (prompt_do_personagem, negative_extra) com o gênero e o tom de pele
    reforçados por tags que o modelo realmente entende.
    """
    corpo = _TAG_GENERO_INICIAL.sub('', desc or '').strip(' ,')
    # O gerador não entende negação: "NOT wearing glasses" / "no hat" acabam PEDINDO óculos e chapéu.
    # Esses trechos vão para o negative.
    partes, proibidos = [], []
    for parte in (p.strip() for p in corpo.split(',')):
        m = re.match(r'(?:not wearing|not|no|without)\s+(.+)', parte, re.IGNORECASE)
        if m:
            proibidos.append(m.group(1))
        elif parte:
            partes.append(parte)
    corpo = ", ".join(partes)
    feminino = genero == "Feminino"
    # Pesos calibrados renderizando no ToonYou: abaixo de 1.6 a pele escura some em boa parte das seeds
    if feminino:
        tags = "(1girl:1.3), (solo:1.3), solo focus, adult woman, mature female"
        negative = "(1boy, male focus, man, facial hair, beard, mustache:1.4), (child, kid:1.2)"
    else:
        tags = "(1boy:1.3), (male focus:1.2), (solo:1.3), solo focus, adult man, mature male"
        negative = "(1girl, female focus, woman, breasts, long eyelashes, makeup:1.4), (child, kid:1.2)"
    negative += ", (multiple girls, multiple boys:1.3)"
    if _PELE_ESCURA.search(corpo):
        tags += f", (dark skin:1.6), ({'dark-skinned female' if feminino else 'dark-skinned male'}:1.6), (brown skin:1.2), very dark skin"
        negative += ", (pale skin, light skin, fair skin, white skin:1.4)"
    if proibidos:
        negative += f", ({', '.join(proibidos)}:1.3)"
    return f"{tags}, {corpo}", negative


def _remover_genero_oposto(texto, genero):
    """Tira pronomes/palavras do gênero oposto (ex.: 'she', 'woman') de ação e cenário."""
    if genero == "Feminino":
        palavras = r"he|him|his|himself|man|men|boy|boys|gentleman|male"
    else:
        palavras = r"she|her|hers|herself|woman|women|girl|girls|lady|female"
    texto = re.sub(rf"\b(?:{palavras})\b", "", texto, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", texto).strip(" ,")


def montar_triptico_prompts(microcenas_raw, personagens_globais, student_name, npc_principal,
                            scenery_guideline="", student_genero="Masculino", npc_visual=""):
    """
    Gera 4 prompts de imagem (storyboard).

    Regras de personagem por quadro:
    - MÁXIMO 1 personagem por quadro (o gerador falha com 2+).
    - O LLM sugere quem aparece em cada microcena via campo 'personagens'.
    - Se a lista tiver >1, usamos apenas o primeiro.
    - Se estiver vazia, é quadro de cenário puro (sem humano).
    - Garantimos que ao menos 1 dos 4 quadros seja cenário puro.

    NPC visual:
    - A descrição vem exatamente do blueprint (npc_global_visual) — não prefixamos
      com '1man,' genérico para evitar contradições.
    """
    import random

    while len(microcenas_raw) < 4:
        microcenas_raw.append(microcenas_raw[-1].copy())

    # Monta mapa nome→descrição visual
    desc_por_nome = {}
    for p in personagens_globais:
        desc_por_nome[p["nome"].lower()] = p["descricao_visual"]

    student_desc = desc_por_nome.get(student_name.lower(), "young adult, short hair, brown eyes, simple period-appropriate clothing")
    # O visual do NPC vem do blueprint (fonte fixa) — o LLM às vezes reescreve e perde detalhes como a cor da pele
    npc_desc     = npc_visual or desc_por_nome.get(npc_principal.lower(), "historical figure, period-appropriate clothing")
    npc_genero   = genero_do_visual(npc_desc)

    student_prompt, student_negative = montar_visual_personagem(student_desc, student_genero)
    npc_prompt, npc_negative         = montar_visual_personagem(npc_desc, npc_genero)

    # Garante que ao menos um quadro seja de cenário puro.
    # Verifica se o LLM já deixou algum com 'personagens' vazio.
    tem_cenario_puro = any(len(mc.get("personagens", [])) == 0 for mc in microcenas_raw[:4])
    if not tem_cenario_puro:
        # Força o quadro 3 (índice 2) a ser cenário puro
        microcenas_raw[2] = dict(microcenas_raw[2])
        microcenas_raw[2]["personagens"] = []

    # Garante que não haja 2 quadros seguidos com o mesmo personagem
    # (alterna NPC → aluno → cenário → NPC etc.)
    ultimo_char = None

    prompts   = []
    textos    = []
    negatives = []   # ← negative_prompt específico por quadro

    for i, cena in enumerate(microcenas_raw[:4]):
        pers = list(cena.get("personagens", []))

        # Máximo 1 personagem
        if len(pers) > 1:
            pers = pers[:1]

        # Resolve o tipo de quadro e define negative correto
        char_prompt   = ""
        negative_quad = NEGATIVE_TOONYOU   # default: quadro com 1 pessoa
        genero_quad   = None               # gênero de quem aparece no quadro

        if len(pers) == 0:
            # Quadro de cenário puro — bloqueia qualquer humano
            char_prompt   = "no humans, no people, scenery only, environmental shot, empty scene"
            negative_quad = NEGATIVE_CENA_PURA
            ultimo_char   = None
        else:
            p_nome = pers[0]
            if p_nome.lower() == student_name.lower():
                ultimo_char = "npc" if ultimo_char == "student" and i < 3 else "student"
            elif p_nome.lower() == npc_principal.lower():
                ultimo_char = "student" if ultimo_char == "npc" and i < 3 else "npc"
            else:
                char_prompt   = "no humans, scenery only, empty scene"
                negative_quad = NEGATIVE_CENA_PURA
                ultimo_char   = None

            # Gênero e pele explícitos de quem aparece + negative com o oposto
            if ultimo_char == "student":
                char_prompt, extra = student_prompt, student_negative
                genero_quad = student_genero
            elif ultimo_char == "npc":
                char_prompt, extra = npc_prompt, npc_negative
                genero_quad = npc_genero
            if genero_quad:
                negative_quad = f"{negative_quad}, {extra}"

        # Texto que vai para o gerador de imagem (Inglês)
        acao_raw = cena.get("action_english", cena.get("acao", "standing, looking around"))
        acao     = _acao_para_keywords(acao_raw, student_name, npc_principal)
        emocao   = cena.get("emotion_english", cena.get("emocao", "neutral"))
        cenario  = cena.get("scenery_english", cena.get("cenario", "detailed period-appropriate background"))
        camera   = cena.get("camera_english", cena.get("camera", "medium shot"))

        # Texto que vai aparecer escrito na tela para o usuário (Português)
        acao_tela = cena.get("acao_ptbr", acao_raw)

        # Se for cenário puro, o LLM frequentemente ainda coloca ações/nomes, quebram a imagem.
        # Filtramos agressivamente.
        if genero_quad is None:
            acao = ""
            emocao = ""
            import re as _re
            # Remove nomes dos personagens do cenário gerado
            for nome_char in [student_name, npc_principal]:
                if nome_char:
                    cenario = _re.sub(r'\b' + _re.escape(nome_char) + r'\b', 'someone', cenario, flags=_re.IGNORECASE)
        else:
            # Quadro com pessoa: nomes ("Katherine's desk") e pronomes do gênero oposto
            # ("she smiles") puxam o gerador para a pessoa errada — removemos.
            for nome_char in [student_name, npc_principal]:
                for parte in (nome_char or "").split():
                    if len(parte) > 2:
                        cenario = re.sub(r"\b" + re.escape(parte) + r"(?:'s)?\b", "", cenario, flags=re.IGNORECASE)
                        acao = re.sub(r"\b" + re.escape(parte) + r"(?:'s)?\b", "", acao, flags=re.IGNORECASE)
            acao    = _remover_genero_oposto(acao, genero_quad) or "standing, neutral pose"
            cenario = _remover_genero_oposto(cenario, genero_quad)

        # Extrai objetos-chave do scenery_guideline como contexto de época
        sg_extra = ""
        if scenery_guideline:
            import re as _re
            objetos = _re.search(r'Key objects?:(.*?)(?:Atmosphere:|$)', scenery_guideline, _re.IGNORECASE | _re.DOTALL)
            if objetos:
                trecho = objetos.group(1).strip()
                trecho = _re.sub(r'\([^)]*\)', '', trecho)
                trecho = _re.sub(r'[.\[\]{}]', '', trecho)
                trecho = _re.sub(r'\s+', ' ', trecho).strip(' ,')
                if len(trecho) > 130:
                    trecho = trecho[:130].rsplit(' ', 1)[0]
                sg_extra = trecho
            else:
                sg_extra = scenery_guideline[:100]

        # Montagem do Prompt
        if genero_quad is None:
            prompt_completo = (
                f"{char_prompt}, {cenario}, {sg_extra}, {camera}, cinematic lighting, "
                f"masterpiece, best quality, highres, anime style, 2d illustration, "
                f"studio ghibli style, vibrant vivid colors, highly detailed scenery, cel shading"
            )
        else:
            prompt_completo = (
                f"{char_prompt}, {acao}, {emocao} expression, "
                f"{cenario}, {sg_extra}, {camera}, cinematic lighting, "
                f"masterpiece, best quality, highres, anime style, 2d illustration, "
                f"studio ghibli style, vibrant vivid colors, highly detailed, cel shading"
            )

        prompts.append(prompt_completo)
        textos.append(acao_tela)
        negatives.append(negative_quad)

    return prompts, textos, negatives


# ============================================================
# GERAÇÃO DE CONTEÚDO (CONTRATADO PELO STATE MANAGER)
# ============================================================

def encontrar_termos(texto, termos):
    """Termos (palavra inteira, sem diferenciar maiúsculas) que aparecem no texto."""
    return [t for t in (termos or [])
            if re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", texto or "", re.IGNORECASE)]


def filtrar_opcoes(opcoes, termos_proibidos, npc, escolhas_anteriores=()):
    """
    Última barreira antes da tela de decisão: descarta opções que citam outra história
    (ex.: "Ajudar Turing..." numa história da Katherine) ou que repetem uma escolha já feita.
    Como a próxima cena nasce da escolha, uma opção contaminada contamina o resto da história.
    """
    feitas = {e.strip().lower() for e in escolhas_anteriores}
    validas = []
    for op in opcoes or []:
        if not isinstance(op, str) or not op.strip():
            continue
        if encontrar_termos(op, termos_proibidos):
            print(f"🚫 Opção descartada (mistura de histórias): {op!r}")
        elif op.strip().lower() in feitas or op.strip().lower() in {v.lower() for v in validas}:
            print(f"🚫 Opção descartada (repetida): {op!r}")
        else:
            validas.append(op.strip())
    npc = npc or "o personagem"
    for reserva in (f"Ajudar {npc} no próximo passo", f"Perguntar a {npc} o que vem a seguir",
                    f"Observar com atenção o que {npc} faz agora"):
        if len(validas) >= 2:
            break
        if reserva.lower() not in feitas:
            validas.append(reserva)
    return validas[:2]


def garantir_marco_no_texto(cena, marco):
    """
    Na cena de um marco histórico, o ano precisa ser dito. O phi4-mini ignora essa regra com
    frequência (e refazer custa ~40 s com o aluno esperando), então, se o ano não veio,
    a cena abre anunciando o marco — o NAO fala e a frase aparece no 1º quadro.
    """
    if marco and marco.get("ano") and marco["ano"] not in cena.get("historia", ""):
        cena["historia"] = f"Ano de {marco['ano']} — {marco['titulo']}. {cena.get('historia', '')}".strip()
    return cena


def cena_de_reserva(ctx):
    """
    Última garantia: se o LLM falhar em todas as tentativas, monta a cena com o conteúdo
    do próprio blueprint (época, fala do NPC em PT-BR, marco) para a história nunca ficar vazia.
    """
    npc = ctx.get("npc_principal") or "o personagem"
    aluno = ctx.get("student_name", "")
    fala = re.search(r"'([^']*[a-zà-ú][^']{8,})'", ctx.get("must_happen", ""))
    partes = [f"{ctx.get('epoca', '')}.".strip(" .") + "." if ctx.get("epoca") else "",
              f"{aluno} está ao lado de {npc}, {'atenta' if ctx.get('student_genero') == 'Feminino' else 'atento'} a cada detalhe."]
    if fala:
        partes.append(f"{npc} diz: '{fala.group(1)}'")
    marco = ctx.get("marco_historico")
    if marco:
        partes.append(marco["evento"])
    print(f"🛟 Cena de reserva usada no passo [{ctx.get('current_step')}] — o LLM falhou em todas as tentativas.")
    microcenas = [
        {"acao_ptbr": f"{npc} explica o momento.", "action_english": "explaining, gesturing", "camera_english": "medium shot", "emotion_english": "focused", "scenery_english": "detailed period-appropriate room", "personagens": [npc]},
        {"acao_ptbr": "O lugar onde tudo acontece.", "action_english": "", "camera_english": "wide establishing shot", "emotion_english": "neutral", "scenery_english": "detailed period-appropriate room, key objects of the era", "personagens": []},
        {"acao_ptbr": f"{aluno} observa com atenção.", "action_english": "listening attentively", "camera_english": "close-up", "emotion_english": "curious", "scenery_english": "detailed period-appropriate room", "personagens": [aluno]},
        {"acao_ptbr": f"{npc} continua o trabalho.", "action_english": "working, focused", "camera_english": "low angle", "emotion_english": "determined", "scenery_english": "detailed period-appropriate desk with documents", "personagens": [npc]},
    ]
    return {"historia": " ".join(p for p in partes if p), "opcoes": [], "personagens": [], "microcenas": microcenas}


def normalizar_cena(dados):
    """
    Garante os tipos do JSON do LLM antes de qualquer uso. O phi4-mini às vezes devolve
    um personagem sem "nome", microcenas como texto solto ou campos como listas — antes
    isso derrubava a rota /escolher (KeyError) e a apresentação travava.
    """
    if not isinstance(dados, dict):
        return {}
    lista = lambda v: v if isinstance(v, list) else []
    texto = lambda v: v.strip() if isinstance(v, str) else ""

    personagens = []
    for p in lista(dados.get("personagens")):
        if isinstance(p, dict) and texto(p.get("nome")):
            personagens.append({"nome": texto(p.get("nome")), "descricao_visual": texto(p.get("descricao_visual"))})

    microcenas = []
    for mc in lista(dados.get("microcenas")):
        if not isinstance(mc, dict):
            continue
        limpa = {k: (v if isinstance(v, str) else " ".join(map(str, v)) if isinstance(v, list) else str(v))
                 for k, v in mc.items() if k != "personagens" and v is not None}
        pers = mc.get("personagens")
        limpa["personagens"] = [x.strip() for x in pers if isinstance(x, str) and x.strip()] if isinstance(pers, list) \
            else ([pers.strip()] if isinstance(pers, str) and pers.strip() else [])
        microcenas.append(limpa)

    return {**dados,
            "historia": texto(dados.get("historia")),
            "opcoes": [texto(o) for o in lista(dados.get("opcoes")) if texto(o)],
            "personagens": personagens,
            "microcenas": microcenas}


def gerar_json_seguro(prompt, temperatura=0.75, max_tentativas=3, termos_proibidos=None):
    """
    termos_proibidos: nomes/termos de OUTRAS histórias. Se aparecerem na "historia" ou
    nas "opcoes", refaz a geração (as opções ainda passam por filtrar_opcoes depois).
    Se nenhuma tentativa passar em tudo, devolve a melhor tentativa com texto — nunca uma cena vazia.
    """
    candidatos = []   # (gravidade dos problemas, dados)
    for tentativa in range(max_tentativas):
        try:
            resposta = ollama.chat(
                model=MODELO, 
                messages=[{'role': 'user', 'content': prompt}], 
                format='json',
                options={
                    # Cada nova tentativa fica mais conservadora: menos chance de JSON quebrado ou laço de repetição
                    'temperature': max(0.3, temperatura - 0.2 * tentativa),
                    'num_predict': 1600,   # suficiente para o JSON completo; menos = mais rápido
                    # O prompt da história tem ~3.500-4.200 tokens. Com 4096 o Ollama cortava o COMEÇO
                    # do prompt (idioma, escolha do jogador, marco) e o modelo só via o schema do fim.
                    'num_ctx': 8192,
                },
                keep_alive=0               # descarrega da VRAM imediatamente — Forge precisa da memória para gerar as imagens
            )
            conteudo = resposta.message.content.strip()
            print(f"\n=== RESPOSTA JSON (Tentativa {tentativa+1}) ===\n{conteudo}\n=====================\n")
            if resposta.prompt_eval_count and resposta.prompt_eval_count < len(prompt) / 6:
                print(f"⚠️ ATENÇÃO: o prompt parece ter sido cortado ({resposta.prompt_eval_count} tokens lidos). Aumente o num_ctx.")

            dados = normalizar_cena(json.loads(conteudo))
            historia = dados.get("historia", "")
            if not historia:
                print(f"⚠️ ATENÇÃO: A IA devolveu a história vazia (Tentativa {tentativa+1}). Refazendo a geração...")
                continue

            # Verificação de idioma (Heurística Simples)
            text_lower = " " + historia.lower().replace(".", " ").replace(",", " ").replace("!", " ").replace("?", " ") + " "
            en_words = [" the ", " and ", " with ", " then ", " he ", " she ", " it ", " was ", " his ", " her ", " to ", " of ", " in ", " but "]
            pt_words = [" o ", " a ", " e ", " com ", " então ", " ele ", " ela ", " foi ", " seu ", " sua ", " para ", " que ", " um ", " uma ", " de ", " em ", " no ", " na ", " mas "]
            
            en_score = sum(text_lower.count(w) for w in en_words)
            pt_score = sum(text_lower.count(w) for w in pt_words)
            em_ingles = en_score > pt_score and en_score > 2   # Só repete se detectar um inglês claro

            opcoes_txt = " ".join(o for o in dados.get("opcoes", []) if isinstance(o, str))
            intrusos = encontrar_termos(f"{historia} {opcoes_txt}", termos_proibidos)

            if em_ingles:
                print(f"⚠️ ATENÇÃO: A IA gerou a história majoritariamente em INGLÊS (EN: {en_score}, PT: {pt_score}). Refazendo a geração...")
            if intrusos:
                print(f"⚠️ ATENÇÃO: A cena misturou outra história ({', '.join(intrusos)}). Refazendo a geração...")
            gravidade = 100 * bool(intrusos) + 10 * em_ingles
            if gravidade == 0:
                return dados
            candidatos.append((gravidade, tentativa, dados))
        except Exception as e:
            print(f"❌ Erro no JSON (Tentativa {tentativa+1}): {e}")

    # Nenhuma tentativa passou em tudo: usa a menos problemática (a mais recente em caso de empate)
    if candidatos:
        gravidade, _, dados = min(candidatos, key=lambda c: (c[0], -c[1]))
        print(f"⚠️ Usando a melhor tentativa disponível (gravidade {gravidade}).")
        return dados
    return {}

def montar_prompt_narrativo(contexto, historico="", student_visual_fixo="",
                            fatos_rag="", instrucao_canonica="", ato=1,
                            escolha_anterior=""):
    genero_instrucao = f"GENDER: {contexto.get('student_genero', 'Masculino')}"

    student_visual_instruction = (
        f"FIXED VISUAL (use EXACTLY as is, do not change): {student_visual_fixo}"
        if student_visual_fixo
        else (
            f"Generate a DETAILED physical description for a {contexto.get('student_genero', 'Masculino')} young adult including: "
            "hair color and style, eye color, skin tone, clothing color and style, "
            "any distinctive feature. Example: '1man, young adult, short messy brown hair, green eyes, "
            "light skin, wearing a white linen shirt and dark brown trousers'. "
            "CRITICAL: The student must look COMPLETELY DIFFERENT from the NPC."
        )
    )

    npc_visual_instruction = ""
    if contexto.get("npc_visual"):
        npc_visual_instruction = f"- THE NPC ({contexto.get('npc_principal')}) VISUAL MUST BE EXACTLY: '{contexto.get('npc_visual')}' (Do not invent or change this)."

    scenery_guideline = contexto.get("scenery_guideline", "")
    scenery_instruction = f"### SCENERY ATMOSPHERE (MANDATORY GUIDELINE) ###\n{scenery_guideline}" if scenery_guideline else ""

    # --- 3-ACT STRUCTURE ---
    ato_descricoes = {
        1: {
            "nome": "ACT 1 — INTRODUCTION & WORLD DISCOVERY",
            "instrucao": (
                "This is Act 1 (the opening). PRIMARY GOALS: rich world-building and character introduction. "
                "Set the scene with immersive sensory details (sounds, smells, textures, lighting). "
                "Introduce the historical figure as a flawed, complex, relatable human being — NOT a textbook name. "
                "Plant the seeds of the central conflict. End the scene pulling the student in with a question or challenge. "
                "The tone should be inviting and full of wonder."
            )
        },
        2: {
            "nome": "ACT 2 — CONFLICT, TENSION & BREAKTHROUGH",
            "instrucao": (
                "This is Act 2 (the heart of the story). This is where DRAMA happens. "
                "Push characters to their limits. Show the real human cost of their work: exhaustion, doubt, injustice, failure before triumph. "
                "Choices must feel weighty and consequential. "
                "If there is a CANONICAL SCENE instruction below, it MUST happen in this chapter. "
                "Do NOT resolve the central tension yet — leave it charged."
            )
        },
        3: {
            "nome": "ACT 3 — CLIMAX, RESOLUTION & LEGACY",
            "instrucao": (
                "This is Act 3 — THE FINAL CHAPTER. Bring the story to its emotional peak and resolution. "
                "Honor the historical figure's legacy with warmth, specificity, and emotional depth. "
                "The student must feel they truly witnessed something historic. "
                "End with genuine meaning: hope, inspiration, or bittersweet reflection. "
                "Do NOT end with a generic goodbye. Make the ending feel earned."
            )
        }
    }
    ato_info = ato_descricoes.get(ato, ato_descricoes[1])

    # --- RAG FACTS SECTION ---
    secao_rag = ""
    if fatos_rag:
        secao_rag = f"""### BANCO DE FATOS HISTÓRICOS (USE COMO A ESPINHA DORSAL DA SUA NARRATIVA) ###
Estes são fatos históricos REAIS e VERIFICADOS. Entrelace-os naturalmente na história.
NÃO fabrique eventos que contradigam estes fatos. Use detalhes específicos (nomes, números, lugares).
{fatos_rag}
"""

    # --- CANONICAL SCENE SECTION ---
    secao_canonica = ""
    if instrucao_canonica:
        secao_canonica = f"""### ⚡ CENA CANÔNICA — INSTRUÇÃO OBRIGATÓRIA DE ALTA PRIORIDADE ⚡ ###
{instrucao_canonica}

REGRA DE COERÊNCIA DA CENA CANÔNICA (CRÍTICO):
- Esta cena DEVE ser mostrada através de uma sequência completa e lógica de causa e efeito.
- NÃO apenas mencione o elemento (uma placa, uma máquina, um telefonema) em uma única frase de passagem.
- Cada frase deve fluir naturalmente para a próxima. A cena canônica deve FAZER SENTIDO no contexto.
- Se a cena envolve uma injustiça (banheiro, café), mostre a ação completa: o personagem anda, vê, reage.
- NÃO combine elementos da cena canônica com pontos de enredo não relacionados na mesma frase.
"""

    # --- MARCOS HISTÓRICOS (2 por jornada) ---
    secao_marco = ""
    marcos = contexto.get("marcos_jornada", [])
    marco = contexto.get("marco_historico")
    if marcos:
        lista_marcos = "\n".join(
            f"- Capítulo {m['capitulo']}: {m['ano']} — {m['titulo']}" for m in marcos
        )
        secao_marco = f"""### MARCOS HISTÓRICOS DA JORNADA ###
Esta jornada tem exatamente {len(marcos)} marcos históricos, cada um no SEU capítulo:
{lista_marcos}
"""
        if marco:
            secao_marco += f"""
### ★ ESTE CAPÍTULO É O MARCO HISTÓRICO: {marco['ano']} — {marco['titulo']} ★ ###
O que aconteceu: {marco['evento']}
REGRAS OBRIGATÓRIAS DO MARCO:
- O marco DEVE ACONTECER diante de {contexto['student_name']} neste capítulo — mostre o momento acontecendo, não apenas mencione.
- A "historia" DEVE citar o ano "{marco['ano']}" e o acontecimento de forma explícita.
- {contexto.get('npc_principal', 'O personagem')} deve explicar, em uma fala direta, por que este momento muda a história.
- Pelo menos 1 microcena deve mostrar visualmente o objeto ou o momento central do marco.
- Mesmo que o ato peça tensão, o marco se completa AQUI; deixe apenas uma nova consequência em aberto para o próximo capítulo.
"""
        else:
            secao_marco += (
                "Este capítulo NÃO é um marco. NÃO antecipe nem resolva os marcos de outros capítulos: "
                "marcos já vividos podem ser lembrados em uma frase; marcos futuros podem apenas ser preparados.\n"
            )

    # --- PLAYER CHOICE SEED ---
    secao_escolha = ""
    if escolha_anterior:
        secao_escolha = f"""### AÇÃO DO JOGADOR — PONTO DE PARTIDA OBRIGATÓRIO ###
O jogador ACABOU de escolher a seguinte ação: "{escolha_anterior}"
CRÍTICO: A sua "historia" gerada DEVE ser a consequência direta e imediata desta escolha.
Mostre {contexto['student_name']} executando essa ação (ou sofrendo as consequências dela) na primeira frase da história. Em seguida, avance o enredo para o próximo passo.
NÃO repita cenas passadas. Crie uma cena ORIGINAL baseada EXCLUSIVAMENTE nesta escolha.
"""
        if contexto.get("salto_temporal") and contexto.get("epoca"):
            secao_escolha += f"""### SALTO NO TEMPO ###
Este capítulo acontece em: {contexto['epoca']} — um tempo DEPOIS do capítulo anterior.
Conclua a escolha do jogador em UMA frase e então deixe o salto explícito com uma marcação de tempo (ex.: "Meses depois...", "Anos mais tarde, em ..."). Só então avance o enredo na nova época.
"""

    # --- HISTORY SECTION (ENRICHED) ---
    if not historico:
        intro_rule = (
            f"- ESTA É A PRIMEIRA CENA. Jogue o estudante diretamente no mundo.\n"
            f"- Comece com um detalhe sensorial específico (um som, um cheiro, um visual).\n"
            f"- Apresente o ambiente e o personagem através do que o estudante vivencia, não através de uma narração seca."
        )
    else:
        acao_label = f"'{escolha_anterior}'" if escolha_anterior else "uma escolha anterior"
        intro_rule = (
            f"- ESTA NÃO É A PRIMEIRA CENA. OBEDEÇA ESTAS REGRAS ANTI-REPETIÇÃO ESTRITAMENTE:\n"
            f"  1. NUNCA comece com '[estudante] entrou' ou qualquer versão de entrar/caminhar para uma sala.\n"
            f"  2. NUNCA repita a descrição do ambiente ({contexto.get('npc_principal', 'o personagem')} na mesa, a sala, etc) — o leitor já sabe.\n"
            f"  3. NUNCA use a frase 'pela décima sétima vez' ou contadores similares.\n"
            f"  4. NUNCA use o padrão de P&R: estudante pergunta 'você precisa de mais dados?' / {contexto.get('npc_principal', 'NPC')} diz 'Sim, preciso'.\n"
            f"  5. A cena DEVE começar IN MEDIAS RES — no meio da ação escolhida pelo jogador: {acao_label}.\n"
            f"  6. Se a escolha foi uma pergunta, a cena COMEÇA com {contexto['student_name']} já terminando de perguntar e a resposta ESPECÍFICA e DETALHADA de {contexto.get('npc_principal', 'the NPC')}.\n"
            f"  7. NÃO repita informações já contadas nos Capítulos Anteriores."
        )

    npc = contexto.get('npc_principal', 'o personagem')

    # --- BLACKLIST ---
    blacklist = f"""### FRASES E PADRÕES PROIBIDOS NO CAMPO "historia" — NUNCA USE ESTES ###
ATENÇÃO: Estas regras se aplicam EXCLUSIVAMENTE ao campo "historia" (texto em PT-BR).
Os campos técnicos de imagem (acao, cenario, emocao) NÃO são afetados por estas regras.
Usar qualquer um destes padrões no "historia" é uma falha crítica:

❌ CLICHÊS DE REAÇÃO FÍSICA (proibido em qualquer variação):
- "[personagem] ergueu os olhos do papel"
- "[personagem] levantou os olhos"
- "[personagem] ergueu a cabeça"
- "[personagem] olhando com uma expressão intensa"
- "[personagem] com uma expressão séria/pensativa/concentrada" como frase solta
- "[personagem] inclina-se para frente" ou qualquer variação de inclinar
- "[personagem] franze as sobrancelhas"
- "[personagem] apertou os lábios"
- "[personagem] respirou fundo" (como gesto vazio sem consequência narrativa)
- "[personagem] sorriu levemente" como encerramento de frase
- "[personagem] observa atentamente" como frase solta sem ação física real
- "[personagem] percebe que..."
- "[personagem] sentiu que..."
- "[{contexto['student_name']}] ficou impressionado/a"

❌ CLICHÊS DE DIÁLOGO:
- "Que escolha interessante!" ou "Boa escolha!"
- "E agora?" ou "O que faremos?" como perguntas vazias
- Qualquer variação de "{npc} disse, sua voz [adjetivo] e [adjetivo]" — ex: "sua voz calma e inspiradora", "sua voz firme e medida"
- Encerrar falas com "...disse ele/ela, sua voz se elevando em excitação"
- Opções genéricas como "Continuar" ou "Explorar" — 'opcoes' DEVEM ser ações físicas e específicas

❌ OUTROS PADRÕES PROIBIDOS:
- Repetir QUALQUER ação ou detalhe de cenário do capítulo anterior
- Descrever pensamentos internos de um personagem SEM nenhuma ação externa acompanhando
- Terminar qualquer frase com "...e sorri" sem contexto claro

✅ SUBSTITUA estes clichês por: ações concretas, detalhes sensoriais do ambiente, fatos históricos específicos, ou consequências diretas da escolha do jogador.
"""

    prompt = f"""[SYSTEM: BILINGUAL STORYBOARD ENGINE — NARRATIVE QUALITY MODE]
Papel: Roteirista Profissional, Diretor de Cinema e Narrador Brasileiro.
Estilo: Studio Ghibli / Pixar — emocionalmente ressonante, visualmente específico, fundamentado historicamente.
Formato de Saída: APENAS JSON Válido.

⚠️⚠️⚠️ LEI ABSOLUTA DE IDIOMA ⚠️⚠️⚠️
Os campos "historia" e "opcoes" DEVEM ser escritos 100% em PORTUGUÊS BRASILEIRO (PT-BR).
Escrever "historia" ou "opcoes" em Inglês é uma FALHA CRÍTICA que QUEBRARÁ todo o sistema.
CRÍTICO: Se você pensar na história em Inglês internamente, você DEVE traduzi-la para um PT-BR perfeito antes de preencher o campo "historia".
Antes de gerar a saída, verifique: cada uma das frases em "historia" está em Português? Se não, reescreva.
Os ÚNICOS campos permitidos em Inglês são os técnicos de imagem: acao, camera, emocao, cenario, descricao_visual.
⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

### ATO NARRATIVO ###
{ato_info['nome']}
{ato_info['instrucao']}

{secao_escolha}
{secao_marco}
{secao_rag}
{secao_canonica}
### PROTOCOLO DOS PERSONAGENS ###
- O Estudante ({contexto['student_name']}) é o PROTAGONISTA e é um JOVEM ADULTO.
- {genero_instrucao}
- REGRA DE PERSPECTIVA CRÍTICA: SEMPRE escreva a "historia" em TERCEIRA PESSOA. Refira-se a {contexto['student_name']} pelo nome. Nunca use "Você" ou "Eu".
- {contexto['student_name']} está FISICAMENTE PRESENTE na cena histórica como um assistente, pesquisador ou engenheiro aprendiz.
- NPCs devem interagir DIRETAMENTE com {contexto['student_name']} — dê a eles diálogos específicos e trejeitos.
- CRÍTICO: {contexto['student_name']} e {contexto.get('npc_principal')} devem ter aparências visuais totalmente diferentes.
{npc_visual_instruction}

### REGRAS DE NARRAÇÃO ###
- A história DEVE ser um parágrafo rico e imersivo (4-6 frases) descrevendo atmosfera E ação.
- O texto será dividido em 4 partes, uma por quadro, e o robô narra cada parte: escreva frases de TAMANHO PARECIDO (evite uma frase enorme ao lado de frases muito curtas).
- Use detalhes sensoriais específicos: o que o estudante VÊ, OUVE, CHEIRA, SENTE.
- Inclua pelo menos UM detalhe histórico específico (um nome real, número, lugar ou máquina).
- NPCs DEVEM ter pelo menos UMA linha de diálogo direto (em PT-BR).
{intro_rule}
- NÃO resuma os acontecimentos — mostre através de ações e reações (Show, don't tell).
- Esta história é EXCLUSIVAMENTE sobre {contexto.get('npc_principal', 'o personagem')} e a sua época. NUNCA traga pessoas, máquinas ou lugares de outras histórias ou de outras figuras históricas.
- As 'opcoes' NUNCA podem repetir uma escolha que o jogador já fez nos capítulos anteriores.

### VISUAL DO ESTUDANTE ###
{student_visual_instruction}

{scenery_instruction}

{blacklist}
### REGRAS DE IDIOMA E JSON SCHEMA (APLICAÇÃO ESTRITA) ###
Retorne APENAS um objeto JSON combinando perfeitamente com este schema:
{{
  "historia": "string ⚠️ EM PORTUGUÊS BRASILEIRO (PT-BR) OBRIGATÓRIO ⚠️ — Parágrafo rico e imersivo (4-6 frases) em TERCEIRA PESSOA. Deve incluir: detalhes sensoriais específicos, pelo menos UMA fala direta do NPC, UM fato histórico real. Conte a história SOBRE {contexto['student_name']}. SE o jogador fez uma escolha (ver seção AÇÃO DO JOGADOR), a primeira frase DEVE mostrar essa escolha acontecendo.",
  "opcoes": [
    "string (PT-BR) — AÇÃO ESPECÍFICA 1 em português, CURTA (até 12 palavras), começando com um verbo: uma ação física de {contexto['student_name']} com {contexto.get('npc_principal', 'o personagem')} ou com um objeto DESTA cena ({contexto.get('epoca', 'desta época')}). NUNCA palavras genéricas.",
    "string (PT-BR) — AÇÃO ESPECÍFICA 2 em português, CURTA (até 12 palavras), começando com um verbo, com consequências diferentes, também sobre ESTA cena."
  ],
  "personagens": [
    {{
      "nome": "string",
      "descricao_visual": "string (MUST BE EN-US) — Exact physical description."
    }}
  ],
  "microcenas": [
    {{
      "acao_ptbr": "string — TEXTO PARA A TELA. STRICTLY IN PORTUGUESE (PT-BR). Descreva a ação que está acontecendo neste quadro para o usuário ler.",
      "action_english": "string — IMAGE PROMPT. STRICTLY IN ENGLISH. Highly descriptive and dynamic action verb phrase for the AI Generator.",
      "camera_english": "string — STRICTLY IN ENGLISH. Camera angle. VARY per microcena.",
      "emotion_english": "string — STRICTLY IN ENGLISH. Character emotion or 'neutral'.",
      "scenery_english": "string — STRICTLY IN ENGLISH. Fully standalone, highly detailed scenery.",
      "personagens": ["string (Character Name, or EMPTY for environment shots)"]
    }}
  ]
}}

[FATAL ERROR WARNING]: Image generator ONLY understands English. 'acao', 'camera', 'emocao', 'cenario' in Portuguese = SYSTEM CRASH.

### MICROCENAS RULES ###
- Generate EXACTLY 4 microcenas.
- Microcenas follow the SAME ORDER as the "historia": microcena 1 illustrates the first quarter of the text, microcena 2 the second, microcena 3 the third, microcena 4 the last.
- At least 1 (max 2) must be an Establishment Shot (empty 'personagens' array) focusing on the environment or a key object.
- Max 1 character per microcena to avoid AI glitches.
- Camera angles MUST be different for each microcena.
- For student microcenas: personagens: ["{contexto['student_name']}"]
- For NPC microcenas: personagens: ["{contexto.get('npc_principal', 'NPC')}"]

### ⛔ MICROCENAS ANTI-REPETITION RULES (CRITICAL) ###
Each microcena "cenario" MUST describe a DISTINCT physical location, object, or angle.
FORBIDDEN patterns in "cenario":
  - Repeating the same machines or objects across ALL 4 cenarios — if you use an object in one, the next must focus on something ELSE from this same era and place (a different object, a window, a close-up of a document, a detail of the room, etc.)
  - Using "same as before", "similar to", or any reference to a previous cenario.
  - Two consecutive cenarios in the same room viewed from the same angle.
Each "acao" must be DIFFERENT from the other 3 — no two microcenas can have the same verb or interaction.
Each "camera" must be DIFFERENT from all others — rotate through close-up, medium shot, wide shot, extreme close-up, low angle, etc.

### TAREFA DA HISTÓRIA ATUAL (CURRENT STORY TASK) ###
Estudante: {contexto['student_name']}
Tema: {contexto['theme']}
Passo Atual: {contexto['current_step']} (Capítulo {contexto.get('step_index', 0) + 1} de {contexto.get('total_steps', 6)})
Época e Lugar: {contexto.get('epoca', '')}
Contexto Histórico: {contexto['historical_facts']}
Objetivo da Cena: {contexto['goal']}
Emoção Principal: {contexto['emotion']}
Obrigatório Acontecer: {contexto['must_happen']}
Proibido Acontecer: {contexto['cannot_happen']}
Histórico: {historico}

[CRITICAL: TECHNICAL METADATA MUST BE IN ENGLISH.]
[CRITICAL: GENERATE EXACTLY 4 MICROCENAS. MAX 1 CHARACTER PER MICROCENA.]
"""

    if contexto.get("is_final"):
        prompt += (
            "\n\nIMPORTANT — THIS IS THE FINAL CHAPTER. Rules:"
            "\n- The 'historia' MUST close the story with an emotionally earned ending. Show the student saying goodbye to the historical figure."
            "\n- Include ONE specific legacy fact (year, award, or lasting impact) spoken aloud by the NPC."
            "\n- The NPC's final line must be a direct, warm farewell addressed to the student by name."
            "\n- The last sentence of 'historia' must feel like a curtain closing — a complete resolution, not a cliffhanger."
            "\n- 'opcoes' should be two warm, reflective choices (e.g., 'Guardar a memória deste encontro' / 'Perguntar o que o futuro reserva')."
            "\n- One microcena must be a wide establishment shot of the location fading to warm light — the visual farewell."
        )

    return prompt

# ============================================================
# CHARACTER SHEET — mantém a aparência do aluno consistente
# ============================================================
def fixar_visual_aluno(personagens, student_name, state):
    """
    Na primeira cena: salva o descricao_visual do aluno no state como 'student_visual_fixed'.
    Nas cenas seguintes: substitui qualquer nova descrição gerada pelo LLM pelo valor salvo,
    garantindo que a aparência seja idêntica em todos os quadros.
    Retorna a lista de personagens com o aluno corrigido.
    """
    student_visual_fixo = state.get("student_visual_fixed")

    aluno_encontrado = False
    for p in personagens:
        if p.get("nome", "").lower() == student_name.lower():
            aluno_encontrado = True
            if not student_visual_fixo and p["descricao_visual"]:
                # Primeira cena: guardar o que o LLM gerou
                state["student_visual_fixed"] = p["descricao_visual"]
                student_visual_fixo = p["descricao_visual"]
            elif student_visual_fixo:
                # Cenas seguintes: blindar a descrição
                p["descricao_visual"] = student_visual_fixo
            break

    # Se a IA esquecer de colocar o aluno na lista, nós adicionamos à força
    if not aluno_encontrado and student_visual_fixo:
        personagens.append({
            "nome": student_name,
            "descricao_visual": student_visual_fixo
        })

    return personagens


def processar_cena(cena_dados, personagens_globais, sid, num_cena, student_name="", npc_principal="", scenery_guideline="",
                   student_genero="Masculino", npc_visual=""):
    microcenas = cena_dados.get("microcenas", [])
    
    if not isinstance(microcenas, list) or len(microcenas) == 0:
        microcenas = [{"acao": "character appearing", "camera": "wide shot", "emocao": "neutral", "cenario": "detailed background", "personagens": [p["nome"] for p in personagens_globais]}]
    
    while len(microcenas) < 4:
        microcenas.append(microcenas[-1].copy())

    # Sistema Clássico: 4 Cenas Completas
    prompts_imagens, textos_quadros, negatives_por_quadro = montar_triptico_prompts(
        microcenas[:4], personagens_globais, student_name, npc_principal,
        scenery_guideline=scenery_guideline, student_genero=student_genero, npc_visual=npc_visual
    )

    nomes_base = []
    for idx, mc in enumerate(microcenas[:4]):
        num_q = idx + 1
        nomes_base.append(f"sessao_{sid}/cena_{num_cena}_quadro_{num_q}.png")

    return {
        "historia": cena_dados.get("historia", ""),
        "fala_robo": cena_dados.get("historia", ""),
        "opcoes": (cena_dados.get("opcoes", []) + ["Continuar", "Explorar"])[:2],
        "prompts_imagens": prompts_imagens,
        "negative_prompts": negatives_por_quadro,   # lista com 1 negative por quadro
        "imagens_arquivos": nomes_base,
        "referencia_arquivo": nomes_base[0],
        "microcenas_textos": textos_quadros
    }


# Variável global para o visualizador (PC2) seguir o que o terminal (PC1) está fazendo
SESSAO_ATIVA = {
    "session_id": None,
    "status": "aguardando", # pode ser: "aguardando", "pensando", "ativo", "modal", "quiz_gerando", "quiz", "quiz_fim"
    "fala_enrolacao": "",
    "last_scene_data": None,
    # --- Sincronização NAO ↔ Imagens ---
    # A rede é instável, então tudo aqui é ESTADO ABSOLUTO (cena X, quadro N), nunca "+1":
    # repetir uma mensagem não muda nada e mensagens de cenas antigas são ignoradas.
    "cena_id": 0,            # muda a cada nova cena
    "quadro_atual": -1,      # índice do quadro (imagem) que o frontend está exibindo agora
    "quadro_desde": 0.0,     # quando o quadro_atual começou (relógio do servidor)
    "quadro_liberado": -1,   # maior quadro já liberado para avançar (NAO, dashboard, painel ou tempo-limite)
    "text_chunks": [],       # lista de strings: texto correspondente a cada quadro
    "nao_falando": False,    # True enquanto o NAO está falando; False quando terminou
    # --- Quiz ---
    "quiz_perguntas": [],    # lista de dicts com pergunta, opcoes, resposta_correta
    "quiz_ids": [],          # IDs das perguntas no banco SQLite
    "quiz_idx_atual": 0,     # índice da pergunta sendo exibida
}
_quadro_lock = threading.Lock()

# Botão "Passar" no painel de decisão aparece depois deste tempo no mesmo quadro
SEGUNDOS_PARA_BOTAO_PASSAR = 10
# Se nenhum sinal chegar (robô travado/sem rede), o quadro libera sozinho depois de
# BASE + tamanho do texto × SEG_POR_CARACTERE (o NAO fala ~13 caracteres por segundo)
TEMPO_LIMITE_BASE = 12
TEMPO_LIMITE_SEG_POR_CARACTERE = 0.09


def _nova_cena_ativa():
    """Zera a sincronização de quadros para uma cena nova."""
    with _quadro_lock:
        SESSAO_ATIVA["cena_id"] = SESSAO_ATIVA.get("cena_id", 0) + 1
        SESSAO_ATIVA["text_chunks"] = []
        SESSAO_ATIVA["quadro_atual"] = -1
        SESSAO_ATIVA["quadro_desde"] = time.time()
        SESSAO_ATIVA["quadro_liberado"] = -1


def _cena_confere(cena_id):
    """Mensagem sem cena_id (clientes antigos) vale para a cena atual; com cena_id, só se bater."""
    return cena_id is None or cena_id == SESSAO_ATIVA["cena_id"]


def _definir_quadro_atual(cena_id, idx):
    """O quadro só anda para frente dentro da mesma cena — reenvios e atrasos não fazem voltar."""
    with _quadro_lock:
        if not _cena_confere(cena_id) or not isinstance(idx, int):
            return False
        if idx > SESSAO_ATIVA["quadro_atual"]:
            SESSAO_ATIVA["quadro_atual"] = idx
            SESSAO_ATIVA["quadro_desde"] = time.time()
        return True


def _liberar_quadro(cena_id, idx, origem):
    """
    Libera o quadro idx para avançar. Idempotente: liberar duas vezes o mesmo quadro
    (clique duplo, reenvio pela rede) não pula nada. Nunca libera um quadro que a
    apresentação ainda não mostrou.
    """
    with _quadro_lock:
        if not _cena_confere(cena_id):
            return False
        atual = SESSAO_ATIVA["quadro_atual"]
        idx = atual if idx is None else min(idx, atual)
        if idx < 0:
            return False
        if idx > SESSAO_ATIVA["quadro_liberado"]:
            SESSAO_ATIVA["quadro_liberado"] = idx
            print(f"⏭️  Quadro {idx + 1} liberado ({origem}) — cena {SESSAO_ATIVA['cena_id']}")
        return True


def _verificar_tempo_limite():
    """Plano B: se nenhum sinal chegou a tempo, libera o quadro sozinho."""
    if SESSAO_ATIVA.get("status") != "ativo":
        return
    atual = SESSAO_ATIVA["quadro_atual"]
    if atual < 0 or SESSAO_ATIVA["quadro_liberado"] >= atual:
        return
    chunks = SESSAO_ATIVA.get("text_chunks", [])
    texto = chunks[atual] if atual < len(chunks) else ""
    limite = TEMPO_LIMITE_BASE + len(texto) * TEMPO_LIMITE_SEG_POR_CARACTERE
    if time.time() - SESSAO_ATIVA["quadro_desde"] > limite:
        _liberar_quadro(SESSAO_ATIVA["cena_id"], atual, f"tempo-limite de {limite:.0f}s")


def _estado_quadros():
    """Campos de sincronização enviados para a apresentação e o painel de decisão."""
    _verificar_tempo_limite()
    atual = SESSAO_ATIVA["quadro_atual"]
    segundos = time.time() - SESSAO_ATIVA["quadro_desde"] if atual >= 0 else 0
    return {
        "cena_id": SESSAO_ATIVA["cena_id"],
        "quadro_atual": atual,
        "quadro_liberado": SESSAO_ATIVA["quadro_liberado"],
        "segundos_no_quadro": round(segundos, 1),
        "pode_passar": (SESSAO_ATIVA.get("status") == "ativo" and atual >= 0
                        and SESSAO_ATIVA["quadro_liberado"] < atual
                        and segundos >= SEGUNDOS_PARA_BOTAO_PASSAR),
    }


ESCOLHA_PENDENTE = None

@app.route('/enviar_escolha', methods=['POST'])
def enviar_escolha():
    global ESCOLHA_PENDENTE
    ESCOLHA_PENDENTE = request.json
    return jsonify({"status": "ok"})

@app.route('/esperar_escolha', methods=['GET'])
def esperar_escolha():
    global ESCOLHA_PENDENTE
    if ESCOLHA_PENDENTE:
        dados = ESCOLHA_PENDENTE
        ESCOLHA_PENDENTE = None
        return jsonify({"status": "ok", "dados": dados})
    return jsonify({"status": "aguardando"})

@app.route('/definir_pensando', methods=['POST'])
def definir_pensando():
    dados = request.json
    SESSAO_ATIVA["status"] = "pensando"
    SESSAO_ATIVA["fala_enrolacao"] = dados.get("frase", "Hmm, deixe-me pensar...")
    SESSAO_ATIVA["nao_falando"] = True   # enquanto pensa/fala, bloqueia avanço
    return jsonify({"status": "ok"})

@app.route('/nao_iniciou_fala', methods=['POST'])
def nao_iniciou_fala():
    """Chamado pelo nao_speaker.py ANTES de iniciar a fala."""
    SESSAO_ATIVA["nao_falando"] = True
    return jsonify({"status": "ok"})

@app.route('/nao_terminou_fala', methods=['POST'])
def nao_terminou_fala():
    """
    Chamado pelo nao_speaker.py APÓS terminar a fala. Se a fala era de um quadro
    ({"cena_id", "quadro_idx"}), libera esse quadro — é o avanço automático da cena.
    O speaker reenvia até receber 200, por isso a operação é idempotente.
    """
    dados = request.get_json(silent=True) or {}
    SESSAO_ATIVA["nao_falando"] = False
    if SESSAO_ATIVA.get("status") == "comando_avulso":
        SESSAO_ATIVA["status"] = "aguardando"
    if isinstance(dados.get("quadro_idx"), int):
        _liberar_quadro(dados.get("cena_id"), dados["quadro_idx"], "NAO terminou de falar")
    return jsonify({"status": "ok", "cena_id": SESSAO_ATIVA["cena_id"]})

@app.route('/nao_terminou', methods=['GET'])
def nao_terminou():
    """
    Polling do frontend: retorna se o NAO terminou de falar o quadro atual.
    Retorna {"terminou": true} quando o NAO está livre.
    """
    terminou = not SESSAO_ATIVA.get("nao_falando", False)
    return jsonify({"terminou": terminou})

@app.route('/enviar_comando_avulso', methods=['POST'])
def enviar_comando_avulso():
    # Proteção: só permite comandos avulsos se a história não estiver rodando
    if SESSAO_ATIVA["status"] not in ["aguardando", "comando_avulso"]:
        return jsonify({"status": "erro", "msg": "Uma história está em andamento! Comandos avulsos só funcionam em modo 'aguardando'."}), 400

    dados = request.json
    if "frase" in dados:
        frase = dados["frase"]
    else:
        nome = dados.get("nome", "Amigo")
        frase = f"Oi {nome}, você quer que eu conte uma história para você?"

    SESSAO_ATIVA["status"] = "comando_avulso"
    SESSAO_ATIVA["fala_comando"] = frase
    return jsonify({"status": "ok"})

@app.route('/publicar_cena', methods=['POST'])
def publicar_cena():
    dados = request.json
    SESSAO_ATIVA["session_id"] = dados.get("session_id")
    SESSAO_ATIVA["last_scene_data"] = dados
    SESSAO_ATIVA["status"] = "ativo"
    return jsonify({"status": "ok"})

@app.route('/publicar_quadro', methods=['POST'])
def publicar_quadro():
    """
    Chamado pelo frontend (index.html) sempre que avança para uma nova imagem.
    Informa ao servidor (e portanto ao nao_speaker.py) qual quadro está visível agora.
    """
    dados = request.get_json(silent=True) or {}
    aceito = _definir_quadro_atual(dados.get("cena_id"), dados.get("quadro_idx", 0))
    return jsonify({"status": "ok" if aceito else "ignorado", "cena_id": SESSAO_ATIVA["cena_id"]})

@app.route('/visualizador/quadro_atual')
def visualizador_quadro():
    """
    Endpoint exclusivo para o nao_speaker.py.
    Retorna o chunk de texto correspondente ao quadro que está sendo exibido agora,
    permitindo que o NAO fale em sincronia com cada imagem.
    """
    chunks = SESSAO_ATIVA.get("text_chunks", [])
    idx = SESSAO_ATIVA.get("quadro_atual", -1)
    texto = chunks[idx] if chunks and 0 <= idx < len(chunks) else ""

    status = SESSAO_ATIVA.get("status", "aguardando")
    if status == "pensando":
        return jsonify({
            "status": "pensando",
            "texto": SESSAO_ATIVA.get("fala_enrolacao", ""),
            "quadro_idx": idx,
            "cena_id": SESSAO_ATIVA["cena_id"]
        })

    return jsonify({
        "status": status,
        "texto": texto,
        "quadro_idx": idx,
        "cena_id": SESSAO_ATIVA["cena_id"],
        "total_quadros": len(chunks)
    })

@app.route('/registrar_chunks', methods=['POST'])
def registrar_chunks():
    """
    Chamado pelo frontend ao detectar uma nova cena com imagens (com reenvio até confirmar).
    Guarda os text_chunks (texto por quadro) para sincronizar a fala do NAO.
    Só vale para a cena atual; não mexe em quadro_atual (reenviar é seguro).
    """
    dados = request.get_json(silent=True) or {}
    if not _cena_confere(dados.get("cena_id")):
        return jsonify({"status": "ignorado", "cena_id": SESSAO_ATIVA["cena_id"]})
    SESSAO_ATIVA["text_chunks"] = dados.get("text_chunks", [])
    return jsonify({"status": "ok", "cena_id": SESSAO_ATIVA["cena_id"]})

@app.route('/publicar_modal', methods=['POST'])
def publicar_modal():
    global ESCOLHA_PENDENTE
    ESCOLHA_PENDENTE = None  # Evita que um clique duplo acidental responda a próxima pergunta
    dados = request.json
    SESSAO_ATIVA["status"] = "modal"
    SESSAO_ATIVA["last_scene_data"] = dados
    return jsonify({"status": "ok"})

# ============================================================
# PONTO DE DECISÃO (página separada: apresentacao/decisao.html)
# ============================================================
# A apresentação (index.html) abre a decisão quando a cena termina;
# a página de decisão consulta /decisao/atual e responde via /decisao/responder.
DECISAO_ATUAL = {
    "id": 0,              # incrementa a cada nova decisão (evita responder decisão antiga)
    "aberta": False,
    "session_id": None,
    "pergunta": "",
    "opcoes": [],
}
_decisao_lock = threading.Lock()

def fechar_decisao():
    with _decisao_lock:
        DECISAO_ATUAL["aberta"] = False

@app.route('/decisao/abrir', methods=['POST'])
def decisao_abrir():
    dados = request.json or {}
    with _decisao_lock:
        # Mesma decisão já aberta (ex.: apresentação recarregada) → mantém o id
        if (DECISAO_ATUAL["aberta"]
                and DECISAO_ATUAL["session_id"] == dados.get("session_id")
                and DECISAO_ATUAL["opcoes"] == dados.get("opcoes", [])):
            return jsonify({"status": "ok", "id": DECISAO_ATUAL["id"]})
        DECISAO_ATUAL["id"] += 1
        DECISAO_ATUAL["aberta"] = True
        DECISAO_ATUAL["session_id"] = dados.get("session_id")
        DECISAO_ATUAL["pergunta"] = dados.get("pergunta", "QUAL É A SUA DECISÃO?")
        DECISAO_ATUAL["opcoes"] = dados.get("opcoes", [])
        return jsonify({"status": "ok", "id": DECISAO_ATUAL["id"]})

@app.route('/decisao/atual', methods=['GET'])
def decisao_atual():
    with _decisao_lock:
        resp = dict(DECISAO_ATUAL)
    resp["status_sessao"] = SESSAO_ATIVA.get("status", "aguardando")
    resp.update(_estado_quadros())   # o painel mostra o botão "Passar" com pode_passar
    return jsonify(resp)

@app.route('/decisao/responder', methods=['POST'])
def decisao_responder():
    """Reserva a resposta da decisão aberta. Só o primeiro clique vence."""
    dados = request.json or {}
    with _decisao_lock:
        if not DECISAO_ATUAL["aberta"] or dados.get("decisao_id") != DECISAO_ATUAL["id"]:
            return jsonify({"status": "erro", "msg": "Decisão já respondida ou expirada"}), 409
        DECISAO_ATUAL["aberta"] = False
        session_id = DECISAO_ATUAL["session_id"]
    SESSAO_ATIVA["status"] = "pensando"
    SESSAO_ATIVA["fala_enrolacao"] = dados.get("frase", "Processando sua escolha...")
    SESSAO_ATIVA["nao_falando"] = True
    return jsonify({"status": "ok", "session_id": session_id})

@app.route('/iniciar_historia', methods=['POST'])
def iniciar():
    dados = request.json
    nome = dados.get('nome', 'Criança')
    skill = dados.get('skill', 'socializacao')
    tema = dados.get('tema', 'Escola')
    genero = dados.get('genero', 'Masculino')
    visual_fixo = dados.get('visual_fixo', '')

    fechar_decisao()
    sid = manager.create_session(nome, skill, tema)
    ctx = manager.get_current_context(sid)

    # Persiste o início da sessão de história no banco
    quiz_manager.criar_sessao_historia(sid, nome, tema, skill, genero)

    # Salva o gênero no estado para persistência
    state = manager.load_state(sid)
    state["student"]["genero"] = genero
    if visual_fixo:
        state["student_visual_fixed"] = visual_fixo

    # RAG + Cena Canônica
    fatos = rag_historico.buscar_fatos(
        npc_nome=ctx.get("npc_principal", ""),
        step_id=ctx.get("current_step", ""),
        goal=ctx.get("goal", ""),
        topk=3
    )
    steps_sessao = [s["id"] for s in state["blueprint"]["steps"]]
    inst_canonica = canonical_scenes.obter_instrucao_canonica(
        skill=skill,
        session_id=sid,
        step_atual=ctx.get("current_step", ""),
        steps_sessao=steps_sessao
    )
    id_cena_sorteada = canonical_scenes.obter_id_cena_sorteada(skill, sid, steps_sessao)
    print(f"✨ Sessão [{sid}] | Marcos sorteados: {state['blueprint'].get('marcos_sorteados')} | Cena canônica sorteada: [{id_cena_sorteada}]")

    prompt = montar_prompt_narrativo(
        ctx,
        student_visual_fixo=visual_fixo,
        fatos_rag=fatos,
        instrucao_canonica=inst_canonica,
        ato=ctx.get("ato", 1)
    )
    marco = ctx.get("marco_historico")
    cena_raw = gerar_json_seguro(prompt, termos_proibidos=ctx.get("termos_proibidos"))
    if not str(cena_raw.get("historia", "")).strip():
        cena_raw = cena_de_reserva(ctx)
    cena_raw = garantir_marco_no_texto(cena_raw, marco)
    cena_raw["opcoes"] = filtrar_opcoes(cena_raw.get("opcoes"), ctx.get("termos_proibidos"), ctx.get("npc_principal"))

    personagens = cena_raw.get("personagens", [])
    if not personagens:
        desc_padrao = "1man" if genero == "Masculino" else "1woman"
        desc_final = visual_fixo if visual_fixo else f"{desc_padrao}, short hair, brown eyes, light skin, period-appropriate clothing"
        personagens = [{"nome": nome, "descricao_visual": desc_final}]

    # Fixa o visual do aluno e salva no state
    personagens = fixar_visual_aluno(personagens, nome, state)
    state["personagens_globais"] = personagens
    state["last_narrative"] = cena_raw.get("historia", "")
    manager.save_state(sid)

    proc = processar_cena(cena_raw, personagens, sid, 1, student_name=nome, npc_principal=ctx.get("npc_principal", ""), scenery_guideline=ctx.get("scenery_guideline", ""),
                          student_genero=genero, npc_visual=ctx.get("npc_visual", ""))

    # Salva a cena 1 no banco
    quiz_manager.salvar_cena(
        session_id=sid,
        ordem=0,
        step_id=ctx.get('current_step', ''),
        ato=ctx.get('ato', 1),
        npc_principal=ctx.get('npc_principal', ''),
        narrativa=cena_raw.get('historia', ''),
        opcoes=proc.get('opcoes', [])
    )


    dados_retorno = {
        'session_id': sid, 'status': 'sucesso', 'node_id': ctx['current_step'],
        'historia_original': proc['historia'],
        'fala_robo': proc['fala_robo'],
        'prompts_imagens': proc['prompts_imagens'],
        'negative_prompts': proc['negative_prompts'],      # array por quadro
        'negative_prompt': proc['negative_prompts'][0] if proc.get('negative_prompts') else NEGATIVE_TOONYOU,  # legado
        'imagens_arquivos': proc['imagens_arquivos'],
        'referencia_arquivo': proc['referencia_arquivo'],
        'microcenas_textos': proc['microcenas_textos'],
        'marco_historico': ctx.get('marco_historico'),
        'opcoes': proc['opcoes'], 'tem_opcoes': True
    }

    # Publica a cena automaticamente no servidor (a cena nova ganha cena_id antes de ficar visível)
    _nova_cena_ativa()
    SESSAO_ATIVA["session_id"] = sid
    SESSAO_ATIVA["last_scene_data"] = dados_retorno
    SESSAO_ATIVA["status"] = "ativo"

    return jsonify(dados_retorno)


@app.route('/escolher', methods=['POST'])
def escolher():
    dados = request.json
    sid = dados.get('session_id')
    escolha = dados.get('escolha_texto', '')

    state = manager.advance_state(sid, escolha)
    if not state: return jsonify({'status': 'erro'}), 400

    # Registra a escolha do aluno na cena anterior
    idx_anterior = state['current_step_idx'] - 1  # advance_state já incrementou
    quiz_manager.registrar_escolha(sid, idx_anterior, escolha)

    ctx = manager.get_current_context(sid)

    if not ctx: return jsonify({'status': 'sucesso', 'tem_opcoes': False, 'historia_original': "Fim da jornada!"})

    # Monta histórico enriquecido (otimizado para não viciar a IA com textos velhos)
    historico_texto = ""
    if state["history"]:
        historico_texto = "### RESUMO DA JORNADA ATÉ AGORA (NÃO REPITA ESTES EVENTOS) ###\n"

        # Extrai frases e diálogos marcantes de TODAS as cenas passadas para bloquear repetição
        frases_usadas = []
        for h in state["history"]:
            narrative = h.get("narrative", "")
            # Captura trechos de diálogos (entre aspas simples ou duplas)
            import re
            dialogos = re.findall(r"[\"\'](.*?)[\"\']", narrative)
            for d in dialogos:
                if len(d) > 10:  # ignora palavras curtas
                    frases_usadas.append(f'"{d.strip()}"')
            # Captura as primeiras 8 palavras de cada frase (padrões de abertura)
            sentences = re.split(r'[.!?]', narrative)
            for s in sentences[:3]:
                words = s.strip().split()
                if len(words) >= 5:
                    frases_usadas.append(f'"{" ".join(words[:7])}..."')

        for i, h in enumerate(state["history"]):
            ato_label = f"Ato {h.get('ato', '?')} ({h['step']})"
            if i == len(state["history"]) - 1:
                # Última cena: envia apenas 1 frase de resumo (não o texto completo)
                narrative = h.get("narrative", "")
                sentences = [s.strip() for s in re.split(r'[.!?]', narrative) if s.strip()]
                resumo = sentences[0] + "." if sentences else narrative[:120]
                historico_texto += f"- {ato_label} [ÚLTIMA CENA — RESUMO]: {resumo}\n"
                historico_texto += f"  → Decisão do jogador a ser executada AGORA: '{h['choice']}'\n"
            else:
                historico_texto += f"- {ato_label} [CENA PASSADA]: O jogador decidiu '{h['choice']}'\n"

        # Injeta o bloqueio explícito de frases e diálogos já usados
        if frases_usadas:
            historico_texto += "\n⛔ BLOQUEIO ABSOLUTO DE REPETIÇÃO — NUNCA USE ESTAS FRASES, DIÁLOGOS OU INÍCIOS DE FRASE:\n"
            for frase in frases_usadas[:15]:  # limita para não explodir o contexto
                historico_texto += f"  - {frase}\n"
            historico_texto += "Usar qualquer uma destas frases ou conceitos já explorados é uma FALHA CRÍTICA. Avance a história com elementos 100% novos.\n"

    # RAG + Cena Canônica
    skill = ctx.get("skill", state["student"].get("focus_skill", ""))
    fatos = rag_historico.buscar_fatos(
        npc_nome=ctx.get("npc_principal", ""),
        step_id=ctx.get("current_step", ""),
        goal=ctx.get("goal", ""),
        topk=3
    )
    inst_canonica = canonical_scenes.obter_instrucao_canonica(
        skill=skill,
        session_id=sid,
        step_atual=ctx.get("current_step", ""),
        steps_sessao=[s["id"] for s in state["blueprint"]["steps"]]
    )

    student_visual_fixo = state.get("student_visual_fixed", "")
    prompt = montar_prompt_narrativo(
        ctx,
        historico_texto,
        student_visual_fixo=student_visual_fixo,
        fatos_rag=fatos,
        instrucao_canonica=inst_canonica,
        ato=ctx.get("ato", 2),
        escolha_anterior=escolha  # <-- A escolha vira o ponto de partida da narrativa
    )
    marco = ctx.get("marco_historico")
    cena_raw = gerar_json_seguro(prompt, termos_proibidos=ctx.get("termos_proibidos"))
    if not str(cena_raw.get("historia", "")).strip():
        cena_raw = cena_de_reserva(ctx)
    cena_raw = garantir_marco_no_texto(cena_raw, marco)
    cena_raw["opcoes"] = filtrar_opcoes(cena_raw.get("opcoes"), ctx.get("termos_proibidos"), ctx.get("npc_principal"),
                                        escolhas_anteriores=[h["choice"] for h in state["history"]])

    # Garante que o visual do aluno nos personagens gerados seja o fixo
    personagens = state.get("personagens_globais", [])
    novos_personagens = cena_raw.get("personagens", [])
    if novos_personagens:
        for np in novos_personagens:
            if np.get("nome", "").lower() != state["student"]["name"].lower():
                nomes_existentes = [p["nome"].lower() for p in personagens]
                if np["nome"].lower() not in nomes_existentes:
                    personagens.append(np)
        fixar_visual_aluno(personagens, state["student"]["name"], state)
        state["personagens_globais"] = personagens

    state["last_narrative"] = cena_raw.get("historia", "")
    manager.save_state(sid)

    num_cena = state["current_step_idx"] + 1
    proc = processar_cena(cena_raw, personagens, sid, num_cena, student_name=state["student"]["name"], npc_principal=ctx.get("npc_principal", ""), scenery_guideline=ctx.get("scenery_guideline", ""),
                          student_genero=state["student"].get("genero", "Masculino"), npc_visual=ctx.get("npc_visual", ""))

    # Salva a nova cena no banco
    quiz_manager.salvar_cena(
        session_id=sid,
        ordem=state['current_step_idx'],
        step_id=ctx.get('current_step', ''),
        ato=ctx.get('ato', 2),
        npc_principal=ctx.get('npc_principal', ''),
        narrativa=cena_raw.get('historia', ''),
        opcoes=proc.get('opcoes', [])
    )

    dados_retorno = {
        'session_id': sid, 'status': 'sucesso', 'node_id': ctx['current_step'],
        'historia_original': proc['historia'],
        'fala_robo': proc['fala_robo'],
        'prompts_imagens': proc['prompts_imagens'],
        'negative_prompts': proc['negative_prompts'],      # array por quadro
        'negative_prompt': proc['negative_prompts'][0] if proc.get('negative_prompts') else NEGATIVE_TOONYOU,  # legado
        'imagens_arquivos': proc['imagens_arquivos'],
        'referencia_arquivo': proc['imagens_arquivos'][0],
        'microcenas_textos': proc['microcenas_textos'],
        'marco_historico': ctx.get('marco_historico'),
        'opcoes': proc['opcoes'], 'tem_opcoes': not ctx.get('is_final', False)
    }

    # Publica a cena automaticamente no servidor (a cena nova ganha cena_id antes de ficar visível)
    _nova_cena_ativa()
    SESSAO_ATIVA["session_id"] = sid
    SESSAO_ATIVA["last_scene_data"] = dados_retorno
    SESSAO_ATIVA["status"] = "ativo"

    return jsonify(dados_retorno)


@app.route('/visualizador/cena_atual')
@app.route('/visualizador/cena_atual/')
def visualizador_cena():
    if not SESSAO_ATIVA["session_id"] and SESSAO_ATIVA["status"] == "aguardando":
        return jsonify({"status": "aguardando"})
        
    if SESSAO_ATIVA["status"] == "pensando":
        return jsonify({
            "status": "pensando",
            "fala_robo": SESSAO_ATIVA["fala_enrolacao"]
        })
        
    if SESSAO_ATIVA["status"] == "comando_avulso":
        return jsonify({
            "status": "comando_avulso",
            "fala_robo": SESSAO_ATIVA.get("fala_comando", "")
        })
        
    if SESSAO_ATIVA["status"] == "modal":
        return jsonify({
            "status": "modal",
            "dados": SESSAO_ATIVA["last_scene_data"]
        })

    if SESSAO_ATIVA["status"] == "quiz_gerando":
        return jsonify({"status": "quiz_gerando"})

    if SESSAO_ATIVA["status"] == "quiz":
        return jsonify({
            "status": "quiz",
            "session_id": SESSAO_ATIVA["session_id"],
            "dados": SESSAO_ATIVA["last_scene_data"]
        })

    if SESSAO_ATIVA["status"] == "historia_fim" or SESSAO_ATIVA["status"] == "quiz_fim":
        return jsonify({
            "status": "historia_fim",
            "session_id": SESSAO_ATIVA["session_id"],
            "dados": SESSAO_ATIVA["last_scene_data"]
        })

    # A apresentação informa em cada consulta o quadro que está mostrando: se um
    # /publicar_quadro se perdeu na rede, o servidor se corrige aqui sozinho.
    try:
        _definir_quadro_atual(int(request.args["cena_id"]), int(request.args["quadro"]))
    except (KeyError, ValueError):
        pass

    return jsonify({
        "status": "ativo",
        "session_id": SESSAO_ATIVA["session_id"],
        "dados": SESSAO_ATIVA["last_scene_data"],
        **_estado_quadros()
    })

@app.route('/forcar_avanco', methods=['POST'])
def forcar_avanco():
    """
    Botões de passar (dashboard e painel de decisão). Libera o quadro que está na tela.
    Com {"cena_id", "quadro"} só vale para aquele quadro — um clique atrasado pela rede
    não passa o quadro seguinte.
    """
    dados = request.get_json(silent=True) or {}
    quadro = dados.get("quadro") if isinstance(dados.get("quadro"), int) else None
    origem = dados.get("origem", "botão")
    aceito = _liberar_quadro(dados.get("cena_id"), quadro, f"botão {origem}")
    return jsonify({"status": "ok" if aceito else "ignorado", **_estado_quadros()})



# ============================================================
# QUIZ — GERAÇÃO E PERSISTÊNCIA
# ============================================================

def montar_prompt_quiz(student_name, historico, marcos=None):
    """
    Monta o prompt para a IA gerar 5 perguntas de múltipla escolha
    baseadas no histórico narrativo da sessão (com pelo menos 1 por marco histórico).
    """
    regra_marcos = ""
    if marcos:
        lista = "; ".join(f"{m['ano']} — {m['titulo']}" for m in marcos)
        regra_marcos = f"\n10. Faça pelo menos 1 pergunta sobre CADA marco histórico da jornada: {lista}."
    resumo_historia = ""
    for h in historico:
        ato = h.get("ato", "?")
        step = h.get("step", "?")
        narrative = h.get("narrative", "")
        choice = h.get("choice", "")
        resumo_historia += f"- [Ato {ato}, Cena '{step}']: {narrative}\n"
        resumo_historia += f"  → O aluno escolheu: '{choice}'\n"

    prompt = f"""[SYSTEM: QUIZ GENERATOR — EDUCATIONAL ASSESSMENT MODE]
Role: Educational Quiz Designer.
Output: Valid JSON only.

Você acabou de narrar uma história histórica para um aluno chamado {student_name}.
Com base nos acontecimentos da história descritos abaixo, gere EXATAMENTE 5 perguntas de múltipla escolha em PORTUGUÊS BRASILEIRO (PT-BR).

### RESUMO DA HISTÓRIA ###
{resumo_historia}

### REGRAS DO QUIZ ###
1. Cada pergunta deve ser baseada diretamente em um FATO REAL mencionado na história acima.
2. Cada pergunta deve ter EXATAMENTE 4 opções.
3. Uma opção deve ser "Não me lembro." (sempre a ÚLTIMA opção, índice 3).
4. Uma opção deve ser a resposta correta.
5. Duas opções devem ser distratores plausíveis, mas incorretos.
6. As perguntas devem ser claras, curtas e adequadas para crianças (8-12 anos).
7. Distribua as perguntas entre os diferentes momentos da história (começo, meio, fim).
8. A opção correta deve estar SEMPRE no primeiro item (índice 0) do array "opcoes". O sistema vai embaralhar automaticamente depois.
9. "Não me lembro." deve estar SEMPRE no índice 3.{regra_marcos}

### JSON SCHEMA ###
Retorne APENAS um objeto JSON:
{{
  "perguntas": [
    {{
      "pergunta": "string — Uma pergunta em PT-BR sobre um fato específico da história",
      "opcoes": [
        "string — A RESPOSTA CORRETA EXATA",
        "string — Distrator 1",
        "string — Distrator 2",
        "Não me lembro."
      ],
      "resposta_correta": 0,
      "ato": 1
    }}
  ]
}}

CRÍTICO: Gere EXATAMENTE 5 perguntas. A resposta correta DEVE ser sempre o primeiro item do array de opções.
"""
    return prompt


def publicar_proxima_pergunta_quiz():
    """Publica no SESSAO_ATIVA a pergunta atual do quiz."""
    idx = SESSAO_ATIVA["quiz_idx_atual"]
    perguntas = SESSAO_ATIVA["quiz_perguntas"]
    ids = SESSAO_ATIVA["quiz_ids"]

    if idx < len(perguntas):
        SESSAO_ATIVA["status"] = "quiz"
        SESSAO_ATIVA["last_scene_data"] = {
            "pergunta_id": ids[idx] if idx < len(ids) else None,
            "dados": perguntas[idx],
            "num_atual": idx + 1,
            "total": len(perguntas)
        }
        print(f"❓ Quiz: Publicando pergunta {idx + 1}/{len(perguntas)}")


@app.route('/finalizar_sessao', methods=['POST'])
def finalizar_sessao():
    """
    Acionado pelo story_client.js ao fim da história.
    Dispara a geração do quiz em background silenciosamente.
    """
    dados = request.json
    sid = dados.get('session_id')
    state = manager.load_state(sid)

    if not state:
        return jsonify({"status": "erro", "msg": "Sessão não encontrada"}), 404

    fechar_decisao()
    # Sinaliza ao frontend que a história terminou, sem iniciar o quiz na tela
    SESSAO_ATIVA["status"] = "historia_fim"
    SESSAO_ATIVA["session_id"] = sid
    SESSAO_ATIVA["quiz_perguntas"] = []
    SESSAO_ATIVA["quiz_ids"] = []
    SESSAO_ATIVA["quiz_idx_atual"] = 0

    def gerar_silencioso():
        import sqlite3
        con = sqlite3.connect(quiz_manager.DB_PATH)
        con.row_factory = sqlite3.Row
        pre_record = con.execute("SELECT pre_id FROM pre_questionarios WHERE session_id = ?", (sid,)).fetchone()
        con.close()
        
        if not pre_record:
            print(f"🚫 Sessão {sid} não possui código (pre_id). O quiz não será gerado.")
            return

        historico = state.get("history", [])
        student_name = state["student"]["name"]
        tema = state["student"].get("theme", "")
        skill = state["student"].get("focus_skill", "")

        print(f"\n🧠 Gerando quiz silencioso para Pós-Questionário [{sid}] - Aluno: {student_name}")

        marcos = [s["marco_historico"] for s in state["blueprint"]["steps"] if s.get("marco_historico")]
        prompt_quiz = montar_prompt_quiz(student_name, historico, marcos)
        quiz_raw = gerar_json_seguro(prompt_quiz, temperatura=0.5)
        perguntas = quiz_raw.get("perguntas", [])

        if not perguntas:
            print("❌ Falha ao gerar perguntas do quiz.")
            return

        # Garante que "Não me lembro." está sempre na posição 3 e embaralha as outras
        import random
        for p in perguntas:
            opcoes = p.get("opcoes", [])
            
            # Pega o texto da resposta correta (deve ser o índice 0 pelo novo prompt, mas tenta ler do índice fornecido pela IA por segurança)
            idx_correta_ia = p.get("resposta_correta", 0)
            if not isinstance(idx_correta_ia, int) or idx_correta_ia >= len(opcoes):
                idx_correta_ia = 0
            texto_correto = opcoes[idx_correta_ia] if opcoes else ""
            
            # Remove "Não me lembro." se estiver em posição errada
            opcoes_sem_nao = [o for o in opcoes if o.strip().lower() != "não me lembro."]
            # Garante exatamente 3 distractors
            while len(opcoes_sem_nao) < 3:
                opcoes_sem_nao.append("Não disponível")
            opcoes_shuffled = opcoes_sem_nao[:3]
            
            # Embaralha apenas as 3 opções!
            random.shuffle(opcoes_shuffled)
            
            # Descobre o novo índice da resposta correta
            novo_idx_correto = 0
            if texto_correto in opcoes_shuffled:
                novo_idx_correto = opcoes_shuffled.index(texto_correto)
                
            p["opcoes"] = opcoes_shuffled + ["Não me lembro."]
            p["resposta_correta"] = novo_idx_correto

        # Persiste no banco SQLite
        quiz_manager.criar_sessao_quiz(sid, student_name, tema, skill)
        quiz_manager.salvar_perguntas(sid, perguntas)
        
        print(f"✅ Quiz gerado e salvo em background para a sessão {sid}")

    threading.Thread(target=gerar_silencioso).start()

    return jsonify({"status": "ok", "msg": "História encerrada. Quiz gerado no backend silenciosamente."})

@app.route('/responder_quiz', methods=['POST'])
def responder_quiz():
    """
    Recebe a resposta do aluno para a pergunta atual.
    Salva no banco e avança para a próxima pergunta (ou finaliza).
    """
    dados = request.json
    sid = dados.get('session_id')
    pergunta_id = dados.get('pergunta_id')
    resposta_idx = dados.get('resposta_idx')

    perguntas = SESSAO_ATIVA.get("quiz_perguntas", [])
    idx_atual = SESSAO_ATIVA.get("quiz_idx_atual", 0)

    if idx_atual >= len(perguntas):
        return jsonify({"status": "erro", "msg": "Índice de pergunta fora do range"}), 400

    resposta_correta_idx = perguntas[idx_atual].get("resposta_correta", 0)
    correta = (resposta_idx == resposta_correta_idx)
    deu_up = (resposta_idx == 3)  # Índice 3 = "Não me lembro."

    # Salva no banco
    if pergunta_id:
        quiz_manager.salvar_resposta(sid, pergunta_id, resposta_idx, correta, deu_up)

    # Avança para a próxima pergunta
    SESSAO_ATIVA["quiz_idx_atual"] += 1
    proximo_idx = SESSAO_ATIVA["quiz_idx_atual"]

    if proximo_idx < len(perguntas):
        publicar_proxima_pergunta_quiz()
        status_retorno = "proxima"
    else:
        # Quiz finalizado
        SESSAO_ATIVA["status"] = "quiz_fim"
        resultado = quiz_manager.get_resultado_sessao(sid)
        SESSAO_ATIVA["last_scene_data"] = {"resultado": resultado}
        status_retorno = "fim"
        print(f"\n🎉 Quiz encerrado! Sessão {sid} | Resultado: {resultado}")

    return jsonify({
        "status": status_retorno,
        "correta": correta,
        "deu_up": deu_up,
        "resposta_correta_idx": resposta_correta_idx
    })


@app.route('/resultados', methods=['GET'])
def ver_resultados():
    """Retorna o resultado agregado de todas as sessões de quiz."""
    session_id = request.args.get('session_id')
    if session_id:
        resultado = quiz_manager.get_resultado_sessao(session_id)
        if not resultado:
            return jsonify({"status": "erro", "msg": "Sessão não encontrada"}), 404
        return jsonify(resultado)
    return jsonify(quiz_manager.get_resultado_geral())


@app.route('/dashboard')
def dashboard():
    """Serve o dashboard HTML de resultados do quiz."""
    pasta_apresentacao = os.path.join(RAIZ_PROJETO, "apresentacao")
    return send_from_directory(pasta_apresentacao, "dashboard.html")


@app.route('/historia_sessao', methods=['GET'])
def historia_sessao():
    """Retorna detalhes completos de uma sessão de história (cenas + escolhas)."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify(quiz_manager.get_historias_geral())
    dados = quiz_manager.get_historia_completa(session_id)
    if not dados:
        return jsonify({'status': 'erro', 'msg': 'Sessão não encontrada'}), 404
    return jsonify(dados)



@app.route('/salvar_likert', methods=['POST'])
def salvar_likert_route():
    dados = request.json
    if not dados:
        return jsonify({"status": "erro", "msg": "Dados não enviados"}), 400
    try:
        session_id = dados.get('session_id', 'pos_avulso')
        secoes = dados.get('secoes', [])
        respostas = dados.get('respostas', {})
        pre_id = dados.get('pre_id')
        
        # 1) Salva o Likert normal
        quiz_manager.salvar_likert(session_id, secoes, respostas, pre_id)
        
        # 2) Verifica se há respostas de quiz no payload e salva
        quiz_answers = {k: v for k, v in respostas.items() if k.startswith("quiz_")}
        if quiz_answers and session_id != 'pos_avulso':
            import sqlite3
            con = sqlite3.connect(quiz_manager.DB_PATH)
            con.row_factory = sqlite3.Row
            try:
                for q_key, resp_idx in quiz_answers.items():
                    pergunta_id = int(q_key.replace("quiz_", ""))
                    p_db = con.execute("SELECT resposta_correta FROM perguntas_quiz WHERE id = ?", (pergunta_id,)).fetchone()
                    if p_db:
                        correta = 1 if resp_idx == p_db['resposta_correta'] else 0
                        quiz_manager.salvar_resposta(session_id, pergunta_id, resp_idx, correta, False)
            finally:
                con.close()
        
        # Se veio um pre_id, atualiza o status dele para pos_respondido
        if pre_id:
            from datetime import datetime as _dt
            agora = _dt.now().isoformat()
            quiz_manager.atualizar_status_pre(pre_id, 'pos_respondido', session_id if session_id != 'pos_avulso' else None)
            quiz_manager.registrar_metrica_tempo(pre_id, 'pos_questionario', agora, agora)
            
        return jsonify({"status": "sucesso"}), 200
    except Exception as e:
        print("Erro ao salvar Likert e Quiz Pós:", e)
        return jsonify({"status": "erro", "msg": str(e)}), 500



@app.route('/likert_resultados', methods=['GET'])
def likert_resultados():
    try:
        dados = quiz_manager.get_likert_geral()
        return jsonify(dados)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/exportar_excel', methods=['GET'])
def exportar_excel():
    """Gera e faz download de um arquivo Excel com todos os resultados do quiz."""
    import tempfile
    nome_arquivo = f"quiz_resultados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    caminho = os.path.join(tempfile.gettempdir(), nome_arquivo)
    try:
        quiz_manager.exportar_excel_geral(caminho)
        return send_file(
            caminho,
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except ImportError as e:
        return jsonify({"status": "erro", "msg": str(e)}), 500
    except Exception as e:
        print(f"❌ Erro ao exportar Excel: {e}")
        return jsonify({"status": "erro", "msg": str(e)}), 500

@app.route('/exportar_analista', methods=['GET'])
def exportar_analista():
    import tempfile
    nome_arquivo = f"dados_analista_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    caminho = os.path.join(tempfile.gettempdir(), nome_arquivo)
    try:
        quiz_manager.exportar_excel_analista(caminho)
        return send_file(
            caminho,
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        print(f"❌ Erro ao exportar Excel Analista: {e}")
        return jsonify({"status": "erro", "msg": str(e)}), 500


# Fila de sessões que o daemon (story_client.js) precisa processar
_daemon_queue = []
_daemon_lock = threading.Lock()

@app.route('/iniciar_daemon', methods=['POST'])
def iniciar_daemon():
    """
    Chamado pelo frontend após o cadastro.
    Enfileira o session_id para que o story_client daemon gere as imagens.
    """
    dados = request.json
    sid = dados.get('session_id')
    if not sid:
        return jsonify({"status": "erro", "msg": "session_id ausente"}), 400
    with _daemon_lock:
        _daemon_queue.append(sid)
    print(f"📡 Daemon notificado para sessão: {sid}")
    return jsonify({"status": "ok"})

@app.route('/daemon_poll', methods=['GET'])
def daemon_poll():
    """
    Endpoint que o story_client daemon fica polling.
    Retorna a próxima sessão a processar (se houver).
    """
    with _daemon_lock:
        if _daemon_queue:
            sid = _daemon_queue.pop(0)
            return jsonify({"status": "ok", "session_id": sid})
    return jsonify({"status": "vazio"})


# ============================================================
# PRÉ-QUESTIONÁRIO — ENDPOINTS
# ============================================================

@app.route('/pre_questionario', methods=['GET'])
def pre_questionario_page():
    return send_from_directory(PASTA_APRESENTACAO, 'pre_questionario.html')

@app.route('/pos_questionario', methods=['GET'])
def pos_questionario_page():
    return send_from_directory(PASTA_APRESENTACAO, 'pos_questionario.html')


@app.route('/obter_quiz_pos', methods=['GET'])
def obter_quiz_pos():
    pre_id = request.args.get('pre_id')
    if not pre_id:
        return jsonify({"status": "erro", "msg": "pre_id não fornecido"}), 400
        
    try:
        # Busca a sessão mais recente desse pre_id
        import sqlite3
        con = sqlite3.connect(quiz_manager.DB_PATH)
        con.row_factory = sqlite3.Row
        pre_record = con.execute("SELECT session_id FROM pre_questionarios WHERE pre_id = ?", (pre_id,)).fetchone()
        
        if not pre_record or not pre_record['session_id']:
            return jsonify({"status": "erro", "msg": "Nenhuma sessão encontrada para este pre_id"}), 404
            
        session_id = pre_record['session_id']
        
        # Pega as perguntas geradas
        perguntas = con.execute("SELECT id, pergunta, opcoes FROM perguntas_quiz WHERE session_id = ? ORDER BY ordem ASC", (session_id,)).fetchall()
        
        if not perguntas:
            return jsonify({"status": "pendente", "session_id": session_id})
            
        perguntas_lista = []
        for p in perguntas:
            try:
                import json
                opcoes = json.loads(p['opcoes'])
            except:
                opcoes = []
            perguntas_lista.append({
                "id": p['id'],
                "pergunta": p['pergunta'],
                "opcoes": opcoes
            })
            
        return jsonify({"status": "ok", "session_id": session_id, "perguntas": perguntas_lista})
    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)}), 500
    finally:
        if 'con' in locals():
            con.close()

@app.route('/salvar_pre_questionario', methods=['POST'])
def salvar_pre_questionario_route():
    """Recebe e salva as respostas do pré-questionário. Retorna o pre_id gerado."""
    dados = request.json
    if not dados:
        return jsonify({"status": "erro", "msg": "Dados não enviados"}), 400
    try:
        pre_id = quiz_manager.salvar_pre_questionario(dados)
        # Registra métrica de tempo do pré-questionário
        tempo = dados.get("tempo_resposta_seg", 0)
        from datetime import datetime as _dt
        fim_iso = _dt.now().isoformat()
        quiz_manager.registrar_metrica_tempo(pre_id, "pre_quest", fim_iso, fim_iso, tempo)
        return jsonify({"status": "sucesso", "pre_id": pre_id})
    except Exception as e:
        print(f"❌ Erro ao salvar pré-questionário: {e}")
        return jsonify({"status": "erro", "msg": str(e)}), 500


@app.route('/atualizar_status_pre', methods=['POST'])
def atualizar_status_pre_route():
    """Atualiza o status de um participante (usado pelas páginas de sessão e pós-quest)."""
    dados = request.json
    pre_id = dados.get("pre_id")
    novo_status = dados.get("status")
    session_id = dados.get("session_id")
    if not pre_id or not novo_status:
        return jsonify({"status": "erro", "msg": "pre_id e status são obrigatórios"}), 400
    try:
        quiz_manager.atualizar_status_pre(pre_id, novo_status, session_id)
        # Registra métricas de tempo por fase
        from datetime import datetime as _dt
        agora = _dt.now().isoformat()
        if novo_status == "em_historia":
            quiz_manager.registrar_metrica_tempo(pre_id, "historia", agora)
        elif novo_status == "historia_concluida":
            quiz_manager.registrar_metrica_tempo(pre_id, "historia", agora, agora)
        elif novo_status == "em_pos_questionario":
            quiz_manager.registrar_metrica_tempo(pre_id, "pos_questionario", agora)
        elif novo_status == "pos_respondido":
            quiz_manager.registrar_metrica_tempo(pre_id, "pos_questionario", agora, agora)
        return jsonify({"status": "sucesso"})
    except Exception as e:
        print(f"❌ Erro ao atualizar status: {e}")
        return jsonify({"status": "erro", "msg": str(e)}), 500


@app.route('/pre_questionario_dados', methods=['GET'])
def get_pre_questionario_route():
    """Retorna os dados de um pré-questionário pelo pre_id."""
    pre_id = request.args.get("pre_id")
    if not pre_id:
        return jsonify({"status": "erro", "msg": "pre_id é obrigatório"}), 400
    dados = quiz_manager.get_pre_questionario(pre_id)
    if not dados:
        return jsonify({"status": "erro", "msg": "Participante não encontrado"}), 404
    return jsonify(dados)


@app.route('/fila_participantes', methods=['GET'])
def fila_participantes():
    """Retorna a lista de participantes para o dashboard."""
    try:
        fila = quiz_manager.get_fila_pre_questionarios()
        return jsonify(fila)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route('/estatisticas_participacao', methods=['GET'])
def estatisticas_participacao():
    """Retorna métricas agregadas de participação."""
    try:
        stats = quiz_manager.get_estatisticas_participacao()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

