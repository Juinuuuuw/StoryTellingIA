# naoguese.py
# ============================================================
# NAOguês — Transliteração Fonética para o TTS do Robô NAO
# ============================================================
# O motor TTS do NAO em "Brazilian" tem dificuldade com vários
# sons do Português Brasileiro. Este módulo pré-processa o texto
# antes de enviá-lo ao robô, substituindo grafias por versões
# que o NAO consegue pronunciar corretamente.
#
# Ordem de aplicação:
#   1. Substituições de palavras inteiras (dicionário exato)
#   2. Substituições de padrões (regex, do mais específico ao mais geral)
#   3. Normalização final
# ============================================================

import re

# ────────────────────────────────────────────────────────────
# 1. DICIONÁRIO DE PALAVRAS INTEIRAS
#    Palavras que o NAO erra de forma consistente.
#    Chave: palavra em minúsculas | Valor: pronúncia NAO
# ────────────────────────────────────────────────────────────
DICIONARIO_PALAVRAS = {
    # --- Palavras com ç / c + e/i ---
    "coração":        "corr-a-sãum",
    "situação":       "situ-a-sãum",
    "ação":           "a-sãum",
    "ações":          "a-soins",
    "informação":     "inform-a-sãum",
    "criança":        "cri-ân-ssa",
    "crianças":       "cri-ân-ssas",
    "ança":           "ân-ssa",
    "ança":           "ân-ssa",
    "aqui":           "aki",
    "que":            "ke",
    "quando":         "kwandu",
    "qual":           "kual",

    # --- Palavras com lh ---
    "trabalho":       "trab-al-yu",
    "trabalha":       "trab-al-ya",
    "trabalhar":      "trab-al-yar",
    "melhor":         "mel-yor",
    "melhora":        "mel-yora",
    "elho":           "el-yu",
    "olha":           "ol-ya",
    "olhar":          "ol-yar",
    "filho":          "fil-yu",
    "filha":          "fil-ya",
    "filhos":         "fil-yus",
    "pilha":          "pil-ya",
    "batalha":        "bat-al-ya",
    "vermelho":       "verm-el-yu",
    "agulha":         "ag-ul-ya",
    "julho":          "jul-yu",

    # --- Palavras com nh ---
    "amanhã":         "amân-yã",
    "manhã":          "mân-yã",
    "caminho":        "kam-in-yu",
    "caminhos":       "kam-in-yus",
    "vinho":          "vin-yu",
    "minha":          "min-ya",
    "minho":          "min-yu",
    "linha":          "lin-ya",
    "sininho":        "sin-in-yu",
    "senhor":         "sen-yor",
    "senhora":        "sen-yora",
    "sonho":          "son-yu",
    "sonhos":         "son-yus",
    "sonhar":         "son-yar",
    "banheiro":       "ban-yeiro",
    "tenho":          "ten-yu",
    "venho":          "ven-yu",
    "ninho":          "nin-yu",
    "pinho":          "pin-yu",
    "rainha":         "ra-in-ya",
    "galinha":        "gal-in-ya",
    "vizinho":        "viz-in-yu",
    "apanhei":        "apan-yei",
    "banho":          "ban-yu",
    "ganhar":         "gan-yar",

    # --- Palavras com ã / ão / ões ---
    "não":            "nãum",
    "são":            "sãum",
    "então":          "entãum",
    "também":         "tambein",
    "alemão":         "alemãum",
    "irmão":          "irmãum",
    "pão":            "pãum",
    "mão":            "mãum",
    "razão":          "razãum",
    "versão":         "versãum",
    "sessão":         "sessãum",
    "padrão":         "padrãum",
    "botão":          "botãum",
    "avião":          "aviãum",
    "leão":           "leãum",

    # --- Palavras com x (sons variados) ---
    "exemplo":        "egzemplu",
    "exato":          "egzatu",
    "existir":        "egzistir",
    "existe":         "egziste",
    "exame":          "egzame",

    # --- Palavras problemáticas gerais ---
    "você":           "vossê",
    "porque":         "porkê",
    "por que":        "por kê",
    "através":        "atraves",
    "países":         "paizes",
    "após":           "aposs",
    "três":           "treis",
    "mês":            "meis",
    "inglês":         "ingleis",
    "português":      "portugueis",
    "francês":        "franseis",
    "japonês":        "japoneis",
    "aliás":          "ali-as",
    "óbvio":          "obviu",
    "próprio":        "propriu",
    "própria":        "propria",
    "século":         "sekkulu",
    "máquina":        "makkina",
    "técnica":        "teknika",
    "físico":         "fiziku",
    "química":        "kimika",
    "matemática":     "matemattika",
    "música":         "muzika",
    "história":       "istoria",
    "histórico":      "istoriku",
    "científico":     "sientifiku",
    "específico":     "espesifiku",
    "público":        "publiku",
    "tráfego":        "trafegu",
}

# ────────────────────────────────────────────────────────────
# 2. REGRAS DE PADRÃO (regex)
#    Aplicadas em sequência — do mais específico ao mais geral.
#    Cada entrada: (padrão_regex, substituição, flags)
# ────────────────────────────────────────────────────────────
REGRAS_REGEX = [

    # === DÍGRAFOS — devem vir ANTES das regras de letra simples ===

    # "lh" → "ly" (colher → colyer, folha → folya)
    (r'lh',           'ly',      re.IGNORECASE),

    # "nh" → "ny" (ninho → ninyu, manhã → manya)
    (r'nh',           'ny',      re.IGNORECASE),

    # "ch" → "x" (chave → xave) — NAO lê "ch" como K em alguns contextos
    (r'ch',           'x',       re.IGNORECASE),

    # === CEDILHA ===
    (r'ç',            'ss',      0),
    (r'Ç',            'Ss',      0),

    # === VOGAIS NASAIS ===
    # ã / ão → "ãum" (tratado no dicionário para palavras exatas)
    # Para casos gerais, mantem o ã e substitui ão no final de sílaba
    (r'ão\b',         'ãum',     re.IGNORECASE),
    (r'ões\b',        'oins',    re.IGNORECASE),
    (r'ãos\b',        'ãuns',    re.IGNORECASE),

    # === VOGAIS COM ACENTO (que o NAO lê errado) ===
    (r'ê',            'ê',       0),   # geralmente ok, mantém
    (r'é',            'é',       0),   # geralmente ok
    (r'â',            'â',       0),   # geralmente ok
    (r'ô',            'ô',       0),   # geralmente ok
    (r'î',            'i',       0),
    (r'û',            'u',       0),

    # === "qu" antes de e/i → "k" ===
    (r'qu(?=[ei])',   'k',       re.IGNORECASE),

    # === "gu" antes de e/i → "g" ===
    (r'gu(?=[ei])',   'g',       re.IGNORECASE),

    # === X com som de Z (ex-) ===
    (r'\bex(?=[aeiouáéíóúâêîôûãõ])', 'egz', re.IGNORECASE),

    # === S entre vogais → lê como Z (já correto na maioria) ===
    # O NAO às vezes lê errado "s" intervocálico — forçamos "z"
    # Apenas para padrões conhecidos:
    (r'(?<=[aeiouáéíóúâêîôûãõ])s(?=[aeiouáéíóúâêîôûãõ])',  'z', re.IGNORECASE),

    # === "rr" → "rr" (vibrante forte — NAO às vezes suaviza) ===
    # Mantém como está, o NAO em ptb costuma lidar bem

    # === Sílabas travadas com M/N antes de consoante (nasalização) ===
    # NOTA: Não aplicamos regra geral de "am\b" pois pega verbos (falaram, vieram, etc.)
    # que o NAO já pronuncia corretamente. Casos específicos ficam no DICIONARIO_PALAVRAS.

    # === Terminações comuns ===
    # "-ção" já pego pelo ão acima
    # "-dade" → "-dadi" (NAO às vezes corta o e final)
    (r'dade\b',       'dadi',    re.IGNORECASE),
    # "-mente" → "-menti"
    (r'mente\b',      'menti',   re.IGNORECASE),
    # "-agem" → "-ajeim"
    (r'agem\b',       'ajeim',   re.IGNORECASE),

    # === Números por extenso problemáticos ===
    # (geralmente o NAO lida bem com dígitos, mas pode falhar em contextos)

    # === Pontuação que causa pausa estranha ===
    # Reticências já tratadas em limpar_texto
]

# ────────────────────────────────────────────────────────────
# 3. FUNÇÃO PRINCIPAL
# ────────────────────────────────────────────────────────────

def para_naoguese(texto: str) -> str:
    """
    Converte um texto em Português Brasileiro para o "NAOguês":
    uma versão fonética que o motor TTS do robô NAO consegue
    pronunciar corretamente.

    Etapas:
      1. Substitui palavras inteiras do dicionário (case-insensitive).
      2. Aplica as regras de regex em sequência.
      3. Normaliza espaços e retorna.
    """
    if not texto:
        return texto

    # ── Etapa 1: dicionário de palavras inteiras ──────────────
    # Usa word-boundary para não substituir partes de palavras
    for palavra, pronúncia in DICIONARIO_PALAVRAS.items():
        padrao = r'\b' + re.escape(palavra) + r'\b'
        texto = re.sub(padrao, pronúncia, texto, flags=re.IGNORECASE)

    # ── Etapa 2: regras de padrão ────────────────────────────
    for padrao, substituto, flags in REGRAS_REGEX:
        texto = re.sub(padrao, substituto, texto, flags=flags)

    # ── Etapa 3: normalização final ──────────────────────────
    texto = re.sub(r'\s{2,}', ' ', texto).strip()

    return texto


# ────────────────────────────────────────────────────────────
# TESTE RÁPIDO (execute: python naoguese.py)
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    exemplos = [
        "Olá! Você está bem?",
        "Não, não quero isso.",
        "A criança tem um coração muito grande.",
        "O trabalho do filho está excelente.",
        "Amanhã cedo vou caminhar pela manhã.",
        "A situação melhorou bastante.",
        "Ele sonhou com a rainha da galinha.",
        "Português é uma língua incrível.",
        "A matemática e a física são importantes.",
        "Então, qual é a solução para este problema?",
        "Senhor Alan Turing, o que você pensa?",
        "A história do século passado foi fascinante.",
        "Ele tem razão sobre essa versão do algoritmo.",
        "As ações da empresa cresceram muito.",
    ]

    print("=" * 60)
    print("TESTE DO NAOguês — Transliteração Fonética")
    print("=" * 60)
    for frase in exemplos:
        resultado = para_naoguese(frase)
        print(f"\n  ORIGINAL : {frase}")
        print(f"  NAOguês  : {resultado}")
    print("\n" + "=" * 60)
