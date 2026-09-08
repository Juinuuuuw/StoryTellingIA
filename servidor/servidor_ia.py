from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import ollama
from datetime import datetime
import os
import re
import json
import threading
from state_manager import manager
import rag_historico
import canonical_scenes
import quiz_manager

quiz_manager.init_db()

app = Flask(__name__)
CORS(app) # Habilita CORS para todas as rotas

MODELO = 'llama3.1'

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
    return send_from_directory(diretorio, filename)

# ============================================================
# CONFIGURAÇÃO DE ESTILO (Estilo Anime 2D)
# ============================================================
ESTILO_TOONYOU = "masterpiece, best quality, highres, anime style, 2d illustration, studio ghibli style, vibrant vivid colors, highly detailed, cel shading"
NEGATIVE_TOONYOU = "3d, cgi, render, 2.5d, photorealistic, realistic, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, (3 people, 4 people, crowd:1.4), merged faces, merged bodies, fused characters, extra person, duplicate character"

# Prompts específicos para personagem isolado (fundo branco/simples para rembg)
ESTILO_CHAR_ISOLADO = "masterpiece, best quality, highres, anime style, 2d illustration, studio ghibli style, vibrant vivid colors, highly detailed, cel shading, simple white background, character sheet, full body, isolated character"
NEGATIVE_CHAR_ISOLADO = "3d, cgi, render, photorealistic, realistic, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, background scenery, detailed background, complex background, gradient background, multiple characters, crowd, merged bodies"

# Prompts específicos para fundo sem personagens
ESTILO_FUNDO = "masterpiece, best quality, highres, anime style, 2d illustration, studio ghibli style, vibrant vivid colors, highly detailed scenery, cel shading, empty scene, background art, environmental concept art, cinematic wide shot"
NEGATIVE_FUNDO = "3d, cgi, render, photorealistic, realistic, lowres, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, people, person, character, human, man, woman, child, boy, girl, figure, silhouette"

def montar_triptico_prompts(microcenas_raw, personagens_globais, student_name, npc_principal):
    """
    Gera 3 prompts distintos (Storyboard Completo).
    Cada prompt é uma cena COMPLETA (fundo + personagens interagindo) para manter a qualidade e consistência.
    """
    while len(microcenas_raw) < 4:
        microcenas_raw.append(microcenas_raw[-1].copy())

    desc_por_nome = {}
    for p in personagens_globais:
        desc_por_nome[p["nome"].lower()] = p["descricao_visual"]

    student_desc = desc_por_nome.get(student_name.lower(), "1child, cute student, period-appropriate clothing")
    npc_desc     = desc_por_nome.get(npc_principal.lower(), "1man, historical figure, period-appropriate clothing")

    prompts = []
    textos = []

    for i, cena in enumerate(microcenas_raw[:4]):
        personagens_presentes = cena.get('personagens', [])
        
        # Monta a descrição física apenas dos personagens que estão na cena
        desc_personagens = []
        for p_nome in personagens_presentes:
            if p_nome.lower() == student_name.lower():
                desc_personagens.append(f"1child, {student_desc}")
            elif p_nome.lower() == npc_principal.lower():
                desc_personagens.append(f"1man, {npc_desc}")
        
        char_prompt = ", ".join(desc_personagens) if desc_personagens else "no humans, scenery focus"
        
        acao = cena.get('acao', 'standing')
        emocao = cena.get('emocao', 'neutral')
        cenario = cena.get('cenario', 'detailed background')
        camera = cena.get('camera', 'medium shot')

        prompt_completo = (
            f"masterpiece, best quality, highres, anime style, 2d illustration, studio ghibli style, vibrant vivid colors, highly detailed, cel shading, "
            f"{char_prompt}, {acao}, {emocao} expression, {cenario}, {camera}, cinematic lighting"
        )
        prompts.append(prompt_completo)
        textos.append(acao)

    return prompts, textos

# ============================================================
# GERAÇÃO DE CONTEÚDO (CONTRATADO PELO STATE MANAGER)
# ============================================================

def gerar_json_seguro(prompt, temperatura=0.75):
    try:
        resposta = ollama.chat(
            model=MODELO, 
            messages=[{'role': 'user', 'content': prompt}], 
            format='json',
            options={'temperature': temperatura, 'num_predict': 2000},
            keep_alive=0
        )
        conteudo = resposta.message.content.strip()
        print(f"\n=== RESPOSTA JSON ===\n{conteudo}\n=====================\n")
        return json.loads(conteudo)
    except Exception as e:
        print(f"❌ Erro no JSON: {e}")
        return {}

def montar_prompt_narrativo(contexto, historico="", student_visual_fixo="",
                            fatos_rag="", instrucao_canonica="", ato=1,
                            escolha_anterior=""):
    genero_instrucao = f"GENDER: {contexto.get('student_genero', 'Masculino')}"

    student_visual_instruction = (
        f"FIXED VISUAL (use EXACTLY as is, do not change): {student_visual_fixo}"
        if student_visual_fixo
        else (
            f"Generate a DETAILED physical description for a {contexto.get('student_genero', 'Masculino')} child (8-12 years old) including: "
            "hair color and style, eye color, skin tone, clothing color and style, "
            "any distinctive feature. Example: '1boy, 10 years old, short messy brown hair, green eyes, "
            "light skin, wearing a white linen shirt and dark brown trousers'. "
            "CRITICAL: The student is a CHILD. They must look COMPLETELY DIFFERENT from the adult NPC."
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
        secao_rag = f"""### HISTORICAL FACTS DATABASE (USE AS THE BACKBONE OF YOUR NARRATIVE) ###
These are REAL, VERIFIED historical facts. Weave them naturally into the story.
Do NOT fabricate events that contradict these. Use specific details (names, numbers, places).
{fatos_rag}
"""

    # --- CANONICAL SCENE SECTION ---
    secao_canonica = ""
    if instrucao_canonica:
        secao_canonica = f"""### ⚡ CANONICAL SCENE — HIGH PRIORITY MANDATORY INSTRUCTION ⚡ ###
{instrucao_canonica}

CANONICAL SCENE COHERENCE RULE (CRITICAL):
- This scene MUST be shown through a complete, logical sequence of cause and effect.
- Do NOT just mention the element (a sign, a machine, a phone call) in a single passing sentence.
- Every sentence must flow naturally into the next. The canonical scene must MAKE SENSE in context.
- If the scene involves an injustice (bathroom, coffee), show the full action: character walks, sees, reacts.
- Do NOT combine canonical scene elements with unrelated plot points in the same sentence.
"""

    # --- PLAYER CHOICE SEED ---
    secao_escolha = ""
    if escolha_anterior:
        secao_escolha = f"""### AÇÃO DO JOGADOR — PONTO DE PARTIDA OBRIGATÓRIO ###
O jogador escolheu: "{escolha_anterior}"
CRÍTICO: A "historia" DEVE começar a partir desta ação. Mostre {contexto['student_name']} fazendo ou
dizendo exatamente o que foi escolhido. Não resuma — dramatize.
Exemplo: se o jogador escolheu 'Perguntar a Katherine sobre os problemas enfrentados',
a historia deve começar com algo como:
"{contexto['student_name']} respirou fundo e virou-se para Katherine. 'Katherine,' disse ele
com cuidado, 'o que foi mais difícil para você aqui na NASA?' A cientista parou de escrever..."
A escolha deve ser a PRIMEIRA ação visível na narrativa, não um contexto de fundo.
"""

    # --- HISTORY SECTION (ENRICHED) ---
    if not historico:
        intro_rule = (
            f"- THIS IS THE FIRST SCENE. Drop the student directly into the world. "
            f"Open with a specific sensory detail (a sound, a smell, a visual). "
            f"Introduce the setting and character through what the student experiences, not narration."
        )
    else:
        acao_label = f"'{escolha_anterior}'" if escolha_anterior else "a previous choice"
        intro_rule = (
            f"- THIS IS NOT THE FIRST SCENE. OBEY THESE ANTI-REPETITION RULES STRICTLY:\n"
            f"  1. NEVER start with '[student] entrou' or any version of entering/walking into a room.\n"
            f"  2. NEVER repeat the setting description (Katherine at her desk, the room, etc.) — reader knows.\n"
            f"  3. NEVER use the phrase 'por décima sétima vez' or similar counters.\n"
            f"  4. NEVER use the Q&A template: student asks 'você precisa de mais dados?' / Katherine says 'Sim, preciso'.\n"
            f"  5. The scene MUST open IN MEDIAS RES — in the middle of the action chosen by the player: {acao_label}.\n"
            f"  6. If the choice was a question, the scene STARTS with {contexto['student_name']} already asking it and Katherine's SPECIFIC, DETAILED response.\n"
            f"  7. DO NOT repeat information already told in the History section."
        )

    # --- BLACKLIST ---
    blacklist = f"""### FORBIDDEN PHRASES AND PATTERNS — NEVER USE THESE ###
Using any of these is a critical failure:
- "[{contexto['student_name']}] inclina-se para frente" (or any variation of leaning)
- "[{contexto['student_name']}] franze as sobrancelhas"
- "[{contexto['student_name']}] observa atentamente" as a standalone sentence without action
- "Que escolha interessante!" or "Boa escolha!"
- "E agora?" or "O que faremos?" as standalone filler sentences
- Repeating ANY action, observation, or setting detail from the previous chapter
- Describing a character's internal thoughts WITHOUT any accompanying external action
- Starting a sentence with "[{contexto['student_name']}] percebe que..."
- Ending any sentence with "...e sorri" without context
- Generic options like "Continuar" or "Explorar" — options MUST be specific actions
"""

    prompt = f"""[SYSTEM: BILINGUAL STORYBOARD ENGINE — NARRATIVE QUALITY MODE]
Role: Professional Screenwriter, Director & Portuguese Narrator.
Style: Studio Ghibli / Pixar — emotionally resonant, visually specific, historically grounded.
Output: Valid JSON only.

⚠️⚠️⚠️ ABSOLUTE LANGUAGE LAW ⚠️⚠️⚠️
The "historia" field MUST be written 100% in BRAZILIAN PORTUGUESE (PT-BR).
Writing "historia" in English is a FATAL ERROR that will BREAK the entire system.
Before outputting, verify: is every single sentence in "historia" in Portuguese? If not, rewrite.
The ONLY fields allowed in English are: acao, camera, emocao, cenario, descricao_visual.
⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

### NARRATIVE ACT ###
{ato_info['nome']}
{ato_info['instrucao']}

{secao_escolha}
{secao_rag}
{secao_canonica}
### CHARACTER PROTOCOL ###
- The Student ({contexto['student_name']}) is the PROTAGONIST and is a CHILD (8-12 years old).
- {genero_instrucao}
- CRITICAL PERSPECTIVE RULE: ALWAYS write the story ("historia") in the THIRD PERSON. Refer to {contexto['student_name']} by name. Never use "Você" or "Eu".
- {contexto['student_name']} is PHYSICALLY PRESENT in the historical scene as an assistant, researcher, or engineer.
- NPCs must interact directly with {contexto['student_name']} — give them specific dialogue and mannerisms.
- CRITICAL: {contexto['student_name']} (CHILD) and {contexto.get('npc_principal')} (ADULT) must have distinct visual descriptions.
{npc_visual_instruction}

### NARRATION RULES ###
- The story MUST be a rich, immersive paragraph (4-6 sentences) describing atmosphere AND action.
- Use specific sensory details: what the student SEES, HEARS, SMELLS, FEELS.
- Include at least ONE piece of specific historical detail (a name, a number, a place, a machine).
- NPCs must have at least ONE line of direct dialogue (in PT-BR).
- {intro_rule}
- Do NOT summarize — show, do not tell.

### STUDENT VISUAL ###
{student_visual_instruction}

{scenery_instruction}

{blacklist}
### JSON SCHEMA & LANGUAGE RULES (STRICT ENFORCEMENT) ###
Return ONLY a JSON object matching this exact schema:
{{
  "historia": "string ⚠️ EM PORTUGUÊS BRASILEIRO (PT-BR) OBRIGATÓRIO ⚠️ — Parágrafo rico e imersivo (4-6 frases) em TERCEIRA PESSOA. Deve incluir: detalhes sensoriais específicos, pelo menos UMA fala direta do NPC, UM fato histórico real. Conte a história SOBRE {contexto['student_name']}. SE o jogador fez uma escolha (ver seção AÇÃO DO JOGADOR), a primeira frase DEVE mostrar essa escolha acontecendo.",
  "opcoes": [
    "string (PT-BR) — SPECIFIC ACTION 1. A concrete, descriptive action or dialogue choice directly tied to THIS scene (e.g., 'Ajudar Turing a ajustar os rotores da Bombe' or 'Perguntar a Katherine sobre os calculos que ela verificou'). NEVER generic words.",
    "string (PT-BR) — SPECIFIC ACTION 2. A completely different concrete action with different consequences."
  ],
  "personagens": [
    {{
      "nome": "string",
      "descricao_visual": "string (MUST BE EN-US) — Exact physical description."
    }}
  ],
  "microcenas": [
    {{
      "acao": "string (MUST BE EN-US) — Highly descriptive and dynamic action verb phrase. NO passive verbs ('looking', 'standing'). Use active physical interactions.",
      "camera": "string (MUST BE EN-US) — Camera angle. VARY per microcena: 'close-up', 'medium shot', 'full body shot', 'low angle', 'high angle', 'dutch angle', 'extreme close-up', 'wide establishment shot'.",
      "emocao": "string (MUST BE EN-US) — Character emotion or 'neutral'.",
      "cenario": "string (MUST BE STRICTLY EN-US) — Fully standalone, highly detailed scenery. NO Portuguese. NO 'same as before'.",
      "personagens": ["string (Character Name, or EMPTY for environment shots)"]
    }}
  ]
}}

[FATAL ERROR WARNING]: Image generator ONLY understands English. 'acao', 'camera', 'emocao', 'cenario' in Portuguese = SYSTEM CRASH.

### MICROCENAS RULES ###
- Generate EXACTLY 4 microcenas.
- At least 1 (max 2) must be an Establishment Shot (empty 'personagens' array) focusing on the environment or a key object.
- Max 1 character per microcena to avoid AI glitches.
- Camera angles MUST be different for each microcena.
- For student microcenas: personagens: ["{contexto['student_name']}"]
- For NPC microcenas: personagens: ["{contexto.get('npc_principal', 'NPC')}"]

### CURRENT STORY TASK ###
Student: {contexto['student_name']}
Theme: {contexto['theme']}
Step: {contexto['current_step']} (Chapter {contexto.get('step_index', 0) + 1} of {contexto.get('total_steps', 6)})
Historical Context: {contexto['historical_facts']}
Goal: {contexto['goal']}
Emotion: {contexto['emotion']}
Must Happen: {contexto['must_happen']}
Forbidden: {contexto['cannot_happen']}
History: {historico}

[CRITICAL: TECHNICAL METADATA MUST BE IN ENGLISH.]
[CRITICAL: GENERATE EXACTLY 4 MICROCENAS. MAX 1 CHARACTER PER MICROCENA.]
"""

    if contexto.get("is_final"):
        prompt += "\nIMPORTANT: FINAL STEP. No 'opcoes' needed (use two warm reflective options). Write a meaningful, specific ending that honors the historical figure's real legacy."

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
            if not student_visual_fixo:
                # Primeira cena: guardar o que o LLM gerou
                state["student_visual_fixed"] = p["descricao_visual"]
                student_visual_fixo = p["descricao_visual"]
            else:
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


def processar_cena(cena_dados, personagens_globais, sid, num_cena, student_name="", npc_principal=""):
    microcenas = cena_dados.get("microcenas", [])
    
    if not isinstance(microcenas, list) or len(microcenas) == 0:
        microcenas = [{"acao": "character appearing", "camera": "wide shot", "emocao": "neutral", "cenario": "detailed background", "personagens": [p["nome"] for p in personagens_globais]}]
    
    while len(microcenas) < 4:
        microcenas.append(microcenas[-1].copy())

    # Sistema Clássico: 4 Cenas Completas
    prompts_imagens, textos_quadros = montar_triptico_prompts(microcenas[:4], personagens_globais, student_name, npc_principal)

    nomes_base = []
    for idx, mc in enumerate(microcenas[:4]):
        num_q = idx + 1
        if len(mc.get("personagens", [])) > 0:
            # Tem personagem: vamos usar AnimateDiff, gerar como GIF
            nomes_base.append(f"sessao_{sid}/cena_{num_cena}_quadro_{num_q}.gif")
        else:
            # Sem personagem: imagem estática única
            nomes_base.append(f"sessao_{sid}/cena_{num_cena}_quadro_{num_q}.png")

    return {
        "historia": cena_dados.get("historia", ""),
        "fala_robo": cena_dados.get("historia", ""),
        "opcoes": (cena_dados.get("opcoes", []) + ["Continuar", "Explorar"])[:2],
        "prompts_imagens": prompts_imagens,
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
    # --- Quiz ---
    "quiz_perguntas": [],    # lista de dicts com pergunta, opcoes, resposta_correta
    "quiz_ids": [],          # IDs das perguntas no banco SQLite
    "quiz_idx_atual": 0,     # índice da pergunta sendo exibida
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
    return jsonify({"status": "ok"})

@app.route('/publicar_cena', methods=['POST'])
def publicar_cena():
    dados = request.json
    SESSAO_ATIVA["session_id"] = dados.get("session_id")
    SESSAO_ATIVA["last_scene_data"] = dados
    SESSAO_ATIVA["status"] = "ativo"
    return jsonify({"status": "ok"})

@app.route('/publicar_modal', methods=['POST'])
def publicar_modal():
    global ESCOLHA_PENDENTE
    ESCOLHA_PENDENTE = None  # Evita que um clique duplo acidental responda a próxima pergunta
    dados = request.json
    SESSAO_ATIVA["status"] = "modal"
    SESSAO_ATIVA["last_scene_data"] = dados
    return jsonify({"status": "ok"})

@app.route('/iniciar_historia', methods=['POST'])
def iniciar():
    dados = request.json
    nome = dados.get('nome', 'Criança')
    skill = dados.get('skill', 'socializacao')
    tema = dados.get('tema', 'Escola')
    genero = dados.get('genero', 'Masculino')
    visual_fixo = dados.get('visual_fixo', '')

    sid = manager.create_session(nome, skill, tema)
    ctx = manager.get_current_context(sid)

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
    inst_canonica = canonical_scenes.obter_instrucao_canonica(
        skill=skill,
        session_id=sid,
        step_atual=ctx.get("current_step", "")
    )
    id_cena_sorteada = canonical_scenes.obter_id_cena_sorteada(skill, sid)
    print(f"✨ Sessão [{sid}] | Cena canônica sorteada: [{id_cena_sorteada}]")

    prompt = montar_prompt_narrativo(
        ctx,
        student_visual_fixo=visual_fixo,
        fatos_rag=fatos,
        instrucao_canonica=inst_canonica,
        ato=ctx.get("ato", 1)
    )
    cena_raw = gerar_json_seguro(prompt)

    personagens = cena_raw.get("personagens", [])
    if not personagens:
        desc_padrao = "1boy" if genero == "Masculino" else "1girl"
        desc_final = visual_fixo if visual_fixo else f"{desc_padrao}, short hair, brown eyes, light skin, period-appropriate clothing"
        personagens = [{"nome": nome, "descricao_visual": desc_final}]

    # Fixa o visual do aluno e salva no state
    personagens = fixar_visual_aluno(personagens, nome, state)
    state["personagens_globais"] = personagens
    state["last_narrative"] = cena_raw.get("historia", "")
    manager.save_state(sid)

    proc = processar_cena(cena_raw, personagens, sid, 1, student_name=nome, npc_principal=ctx.get("npc_principal", ""))

    return jsonify({
        'session_id': sid, 'status': 'sucesso', 'node_id': ctx['current_step'],
        'historia_original': proc['historia'],
        'fala_robo': proc['fala_robo'],
        'prompts_imagens': proc['prompts_imagens'],
        'imagens_arquivos': proc['imagens_arquivos'],
        'referencia_arquivo': proc['referencia_arquivo'],
        'microcenas_textos': proc['microcenas_textos'],
        'negative_prompt': NEGATIVE_TOONYOU,
        'negative_prompt_char': NEGATIVE_CHAR_ISOLADO,
        'opcoes': proc['opcoes'], 'tem_opcoes': True
    })

@app.route('/escolher', methods=['POST'])
def escolher():
    dados = request.json
    sid = dados.get('session_id')
    escolha = dados.get('escolha_texto', '')

    state = manager.advance_state(sid, escolha)
    if not state: return jsonify({'status': 'erro'}), 400

    ctx = manager.get_current_context(sid)
    if not ctx: return jsonify({'status': 'sucesso', 'tem_opcoes': False, 'historia_original': "Fim da jornada!"})

    # Monta histórico enriquecido
    historico_texto = ""
    if state["history"]:
        historico_texto = "### PREVIOUS CHAPTERS (FOR CONTINUITY — DO NOT REPEAT THESE EVENTS) ###\n"
        for h in state["history"]:
            ato_label = f"Act {h.get('ato', '?')}"
            historico_texto += f"- [{ato_label}, step '{h['step']}', emotion: {h.get('emotion', 'unknown')}]: {h.get('narrative', '')}\n"
            historico_texto += f"  → Player chose to: '{h['choice']}'\n"

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
        step_atual=ctx.get("current_step", "")
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
    cena_raw = gerar_json_seguro(prompt)

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
    proc = processar_cena(cena_raw, personagens, sid, num_cena, student_name=state["student"]["name"], npc_principal=ctx.get("npc_principal", ""))

    return jsonify({
        'session_id': sid, 'status': 'sucesso', 'node_id': ctx['current_step'],
        'historia_original': proc['historia'],
        'fala_robo': proc['fala_robo'],
        'prompts_imagens': proc['prompts_imagens'],
        'imagens_arquivos': proc['imagens_arquivos'],
        'referencia_arquivo': proc['imagens_arquivos'][0],
        'microcenas_textos': proc['microcenas_textos'],
        'negative_prompt': NEGATIVE_TOONYOU,
        'negative_prompt_char': NEGATIVE_CHAR_ISOLADO,
        'opcoes': proc['opcoes'], 'tem_opcoes': not ctx.get('is_final', False)
    })

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

    if SESSAO_ATIVA["status"] == "quiz_fim":
        return jsonify({
            "status": "quiz_fim",
            "session_id": SESSAO_ATIVA["session_id"],
            "dados": SESSAO_ATIVA["last_scene_data"]
        })

    return jsonify({
        "status": "ativo",
        "session_id": SESSAO_ATIVA["session_id"],
        "dados": SESSAO_ATIVA["last_scene_data"]
    })



# ============================================================
# QUIZ — GERAÇÃO E PERSISTÊNCIA
# ============================================================

def montar_prompt_quiz(student_name, historico):
    """
    Monta o prompt para a IA gerar 3 perguntas de múltipla escolha
    baseadas no histórico narrativo da sessão.
    """
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

You just narrated a historical story to a student named {student_name}.
Based on the story events described below, generate EXACTLY 3 multiple-choice questions in BRAZILIAN PORTUGUESE (PT-BR).

### STORY SUMMARY ###
{resumo_historia}

### QUIZ RULES ###
1. Each question must be directly based on a REAL fact mentioned in the story above.
2. Each question must have EXACTLY 4 options.
3. One option must be "Não me lembro." (always the LAST option, index 3).
4. One option must be the correct answer.
5. Two options must be plausible but incorrect distractors.
6. Questions must be clear, short, and appropriate for children (8-12 years old).
7. Spread questions across different moments of the story (beginning, middle, end).
8. The "resposta_correta" field must be the INDEX (0, 1, 2, or 3) of the correct option in the "opcoes" array.
9. "Não me lembro." must ALWAYS be at index 3.

### JSON SCHEMA ###
Return ONLY a JSON object:
{{
  "perguntas": [
    {{
      "pergunta": "string — A question in PT-BR about a specific fact from the story",
      "opcoes": [
        "string — Correct answer OR distractor",
        "string — Distractor",
        "string — Distractor",
        "Não me lembro."
      ],
      "resposta_correta": 0,
      "ato": 1
    }}
  ]
}}

CRITICAL: Generate EXACTLY 3 perguntas. All text in PT-BR. "Não me lembro." must be the last option (index 3) in every question.
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
    Dispara a geração do quiz em background e atualiza o status para o frontend.
    """
    dados = request.json
    sid = dados.get('session_id')
    state = manager.load_state(sid)

    if not state:
        return jsonify({"status": "erro", "msg": "Sessão não encontrada"}), 404

    # Sinaliza ao frontend que o quiz está sendo gerado (loading)
    SESSAO_ATIVA["status"] = "quiz_gerando"
    SESSAO_ATIVA["session_id"] = sid
    SESSAO_ATIVA["quiz_perguntas"] = []
    SESSAO_ATIVA["quiz_ids"] = []
    SESSAO_ATIVA["quiz_idx_atual"] = 0

    def gerar_e_publicar():
        historico = state.get("history", [])
        student_name = state["student"]["name"]
        tema = state["student"].get("theme", "")
        skill = state["student"].get("focus_skill", "")

        print(f"\n🧠 Gerando quiz para sessão [{sid}] — Aluno: {student_name}")

        prompt_quiz = montar_prompt_quiz(student_name, historico)
        quiz_raw = gerar_json_seguro(prompt_quiz, temperatura=0.5)
        perguntas = quiz_raw.get("perguntas", [])

        if not perguntas:
            print("❌ IA não gerou perguntas. Usando fallback vazio.")
            SESSAO_ATIVA["status"] = "quiz_fim"
            return

        # Garante que "Não me lembro." está sempre na posição 3
        for p in perguntas:
            opcoes = p.get("opcoes", [])
            # Remove "Não me lembro." se estiver em posição errada
            opcoes_sem_nao = [o for o in opcoes if o.strip().lower() != "não me lembro."]
            # Garante exatamente 3 distractors + "Não me lembro." no final
            while len(opcoes_sem_nao) < 3:
                opcoes_sem_nao.append("Não disponível")
            p["opcoes"] = opcoes_sem_nao[:3] + ["Não me lembro."]

        # Persiste no banco SQLite
        quiz_manager.criar_sessao_quiz(sid, student_name, tema, skill)
        ids = quiz_manager.salvar_perguntas(sid, perguntas)

        SESSAO_ATIVA["quiz_perguntas"] = perguntas
        SESSAO_ATIVA["quiz_ids"] = ids
        SESSAO_ATIVA["quiz_idx_atual"] = 0

        publicar_proxima_pergunta_quiz()

    threading.Thread(target=gerar_e_publicar, daemon=True).start()
    return jsonify({"status": "ok", "msg": "Quiz sendo gerado..."})


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
