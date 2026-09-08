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

def gerar_json_seguro(prompt, temperatura=0.75, max_tentativas=3):
    conteudo = "{}"
    for tentativa in range(max_tentativas):
        try:
            resposta = ollama.chat(
                model=MODELO, 
                messages=[{'role': 'user', 'content': prompt}], 
                format='json',
                options={'temperature': temperatura, 'num_predict': 2000},
                keep_alive=0
            )
            conteudo = resposta.message.content.strip()
            print(f"\n=== RESPOSTA JSON (Tentativa {tentativa+1}) ===\n{conteudo}\n=====================\n")
            
            dados = json.loads(conteudo)
            historia = dados.get("historia", "")
            
            # Verificação de idioma (Heurística Simples)
            text_lower = " " + historia.lower().replace(".", " ").replace(",", " ").replace("!", " ").replace("?", " ") + " "
            en_words = [" the ", " and ", " with ", " then ", " he ", " she ", " it ", " was ", " his ", " her ", " to ", " of ", " in ", " but "]
            pt_words = [" o ", " a ", " e ", " com ", " então ", " ele ", " ela ", " foi ", " seu ", " sua ", " para ", " que ", " um ", " uma ", " de ", " em ", " no ", " na ", " mas "]
            
            en_score = sum(text_lower.count(w) for w in en_words)
            pt_score = sum(text_lower.count(w) for w in pt_words)
            
            if en_score > pt_score and en_score > 2: # Só repete se detectar um inglês claro
                print(f"⚠️ ATENÇÃO: A IA gerou a história majoritariamente em INGLÊS (EN: {en_score}, PT: {pt_score}). Refazendo a geração...")
                continue
                
            return dados
        except Exception as e:
            print(f"❌ Erro no JSON (Tentativa {tentativa+1}): {e}")
            
    # Fallback final se falhar em todas as tentativas
    try:
        return json.loads(conteudo)
    except:
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

    # --- PLAYER CHOICE SEED ---
    secao_escolha = ""
    if escolha_anterior:
        secao_escolha = f"""### AÇÃO DO JOGADOR — PONTO DE PARTIDA OBRIGATÓRIO ###
O jogador ACABOU de escolher a seguinte ação: "{escolha_anterior}"
CRÍTICO: A sua "historia" gerada DEVE ser a consequência direta e imediata desta escolha.
Mostre {contexto['student_name']} executando essa ação (ou sofrendo as consequências dela) na primeira frase da história. Em seguida, avance o enredo para o próximo passo.
NÃO repita cenas passadas. Crie uma cena ORIGINAL baseada EXCLUSIVAMENTE nesta escolha.
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
{secao_rag}
{secao_canonica}
### PROTOCOLO DOS PERSONAGENS ###
- O Estudante ({contexto['student_name']}) é o PROTAGONISTA e é uma CRIANÇA (8-12 anos de idade).
- {genero_instrucao}
- REGRA DE PERSPECTIVA CRÍTICA: SEMPRE escreva a "historia" em TERCEIRA PESSOA. Refira-se a {contexto['student_name']} pelo nome. Nunca use "Você" ou "Eu".
- {contexto['student_name']} está FISICAMENTE PRESENTE na cena histórica como um assistente, pesquisador ou engenheiro aprendiz.
- NPCs devem interagir DIRETAMENTE com {contexto['student_name']} — dê a eles diálogos específicos e trejeitos.
- CRÍTICO: {contexto['student_name']} (CRIANÇA) e {contexto.get('npc_principal')} (ADULTO) devem ter aparências visuais totalmente diferentes.
{npc_visual_instruction}

### REGRAS DE NARRAÇÃO ###
- A história DEVE ser um parágrafo rico e imersivo (4-6 frases) descrevendo atmosfera E ação.
- Use detalhes sensoriais específicos: o que o estudante VÊ, OUVE, CHEIRA, SENTE.
- Inclua pelo menos UM detalhe histórico específico (um nome real, número, lugar ou máquina).
- NPCs DEVEM ter pelo menos UMA linha de diálogo direto (em PT-BR).
{intro_rule}
- NÃO resuma os acontecimentos — mostre através de ações e reações (Show, don't tell).

### VISUAL DO ESTUDANTE ###
{student_visual_instruction}

{scenery_instruction}

{blacklist}
### REGRAS DE IDIOMA E JSON SCHEMA (APLICAÇÃO ESTRITA) ###
Retorne APENAS um objeto JSON combinando perfeitamente com este schema:
{{
  "historia": "string ⚠️ EM PORTUGUÊS BRASILEIRO (PT-BR) OBRIGATÓRIO ⚠️ — Parágrafo rico e imersivo (4-6 frases) em TERCEIRA PESSOA. Deve incluir: detalhes sensoriais específicos, pelo menos UMA fala direta do NPC, UM fato histórico real. Conte a história SOBRE {contexto['student_name']}. SE o jogador fez uma escolha (ver seção AÇÃO DO JOGADOR), a primeira frase DEVE mostrar essa escolha acontecendo.",
  "opcoes": [
    "string (PT-BR) — AÇÃO ESPECÍFICA 1 em português. Ex: 'Ajudar Turing a ajustar os rotores da Bombe'. NUNCA palavras genéricas.",
    "string (PT-BR) — AÇÃO ESPECÍFICA 2 em português com consequências diferentes."
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

### TAREFA DA HISTÓRIA ATUAL (CURRENT STORY TASK) ###
Estudante: {contexto['student_name']}
Tema: {contexto['theme']}
Passo Atual: {contexto['current_step']} (Capítulo {contexto.get('step_index', 0) + 1} de {contexto.get('total_steps', 6)})
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
8. O campo "resposta_correta" deve ser o ÍNDICE (0, 1, 2 ou 3) da opção correta no array "opcoes".
9. "Não me lembro." deve estar SEMPRE no índice 3.

### JSON SCHEMA ###
Retorne APENAS um objeto JSON:
{{
  "perguntas": [
    {{
      "pergunta": "string — Uma pergunta em PT-BR sobre um fato específico da história",
      "opcoes": [
        "string — Resposta correta OU distrator",
        "string — Distrator",
        "string — Distrator",
        "Não me lembro."
      ],
      "resposta_correta": 0,
      "ato": 1
    }}
  ]
}}

CRÍTICO: Gere EXATAMENTE 5 perguntas. Todo o texto em PT-BR. "Não me lembro." deve ser sempre a última opção (índice 3) em cada pergunta.
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
