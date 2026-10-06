"""
canonical_scenes.py — Cenas canônicas marcantes (uma por sessão).

Cada personagem tem um conjunto de cenas icônicas baseadas nos filmes/documentários
(ex: o banheiro de Katherine, a Bombe de Turing). A cada sessão, UMA dessas cenas
é sorteada de forma determinística (baseada no session_id) e injetada como instrução
obrigatória no step ideal da narrativa.

Isso garante que a criança sempre vivencie UM momento marcante diferente em cada
sessão, sem sobrecarregar a história com todos de uma vez.
"""

import hashlib


# ============================================================
# BANCO DE CENAS CANÔNICAS
# ============================================================
CENAS_CANONICAS = {
    "alan_turing": [
        {
            "id": "bombe_noite",
            "step_ideal": ["bombe_victory_preparacao", "enigma_naval_preparacao"],
            "instrucao_prompt": (
                "CANONICAL SCENE — MANDATORY (must be woven naturally into this chapter's narrative): "
                "At some point in this scene, Alan Turing is found asleep slumped against the Bombe machine very late at night. "
                "The machine clicks rhythmically, relays switching, rotors spinning. Turing wakes with a start when the configuration changes. "
                "The student witnesses this moment of absolute, exhausted dedication. "
                "Write this with rich sensory detail: the smell of warm machine oil, the cold stone floor of Bletchley Park, "
                "the dim yellow light, the rhythmic clicking. This is NOT a summary — show it happening in real time."
            )
        },
        {
            "id": "primeiro_codigo_enigma",
            "step_ideal": "enigma_naval",
            "instrucao_prompt": (
                "CANONICAL SCENE — MANDATORY (must be woven naturally into this chapter's narrative): "
                "The Bombe machine suddenly stops. A deafening silence falls over the room. "
                "Then, slowly, the first decoded German naval message is confirmed. "
                "Turing reads the decrypted text aloud, very quietly. His hands tremble slightly. "
                "The student is standing right beside him in this historic moment. "
                "Write with emotional weight: they just potentially changed the course of the war, "
                "but no one can celebrate — because if the Germans know their code is broken, they will change it immediately."
            )
        },
        {
            "id": "injustica_apos_guerra",
            "step_ideal": "legado_turing",
            "instrucao_prompt": (
                "CANONICAL SCENE — MANDATORY (must be woven naturally into this chapter's narrative): "
                "Turing mentions quietly, almost as an aside, that the British government has brought charges against him "
                "for being who he is — loving another man. He is not dramatic about it. He says something like: "
                "'The machine does not judge. It simply follows its instructions. I sometimes wish people were the same.' "
                "The student must feel the profound injustice of this. "
                "Do NOT be preachy — show the unfairness through Turing's calm dignity, not through lecturing."
            )
        },
        {
            "id": "maca_presente",
            "step_ideal": "legado_turing",
            "instrucao_prompt": (
                "CANONICAL SCENE — MANDATORY (must be woven naturally into this chapter's narrative): "
                "Turing hands the student an apple and says: 'Every great idea begins with something simple. "
                "An apple fell on Newton. A piece of tape gave me the machine.' "
                "It is a warm, almost playful moment — but write it with a bittersweet undercurrent. "
                "The apple is a symbol: of discovery, of his legacy, and of the tragic way his story would end. "
                "The student should not know the full weight of it yet — but the reader should feel it."
            )
        }
    ],

    "katherine_johnson": [
        {
            "id": "banheiro_segregado",
            "step_ideal": ["sputnik_corrida_preparacao", "primeira_autora_preparacao", "freedom7_preparacao"],
            "instrucao_prompt": (
                "CANONICAL SCENE — MANDATORY (must be woven naturally into this chapter's narrative): "
                "At some point, Katherine needs to use the bathroom and must walk almost 800 meters to the 'Colored Restroom' in another building. "
                "The student notices Katherine putting on her coat and asks where she is going. "
                "Katherine explains matter-of-factly, without anger or self-pity, as if it were simply the weather: "
                "'The nearest bathroom I am allowed to use is in the East Building. I will be back in twenty minutes.' "
                "She walks out. The student stands there, stunned. "
                "Write this scene with the absurdity shown through action, NOT through the student's moral outrage. "
                "Show the mundane cruelty of segregation: the coat, the walk, the clock on the wall."
            )
        },
        {
            "id": "cafe_segregado",
            "step_ideal": ["sputnik_corrida_preparacao", "primeira_autora_preparacao", "freedom7_preparacao"],
            "instrucao_prompt": (
                "CANONICAL SCENE — MANDATORY (must be woven naturally into this chapter's narrative): "
                "During a break, the student notices there are two identical coffee machines in the break room. "
                "One has a small, worn sticker: 'Colored'. Katherine uses that one, without hesitation, as if it is completely normal. "
                "When the student asks why, Katherine pauses, looks at the machine, and says something quietly profound — "
                "perhaps: 'It is just a machine. The coffee tastes the same. I have bigger problems to solve.' "
                "Write this with the smell of coffee, the hum of the machines, and the uncomfortable silence that follows."
            )
        },
        {
            "id": "glenn_pediu_por_ela",
            "step_ideal": "friendship7_preparacao",
            "instrucao_prompt": (
                "CANONICAL SCENE — MANDATORY (must be woven naturally into this chapter's narrative): "
                "A phone rings. An engineer answers and goes pale. He announces: John Glenn will not board the rocket "
                "until Katherine Johnson personally verifies the IBM computer's trajectory numbers. "
                "The IBM engineers are offended. But the student watches as Katherine simply sits down, "
                "picks up her pencil, and begins checking from the very first line — calm, focused, unstoppable. "
                "Write this as a race against time: the rocket is fueled, Glenn is in his suit, "
                "and Katherine's pencil scratches paper number by number."
            )
        },
        {
            "id": "apollo_13_corrida",
            "step_ideal": "apollo13_preparacao",
            "instrucao_prompt": (
                "CANONICAL SCENE — MANDATORY (must be woven naturally into this chapter's narrative): "
                "The room erupts into controlled chaos. 'Houston, we have a problem.' "
                "Three astronauts, 330,000 km away, have oxygen for only a few more hours. "
                "Katherine does not panic. She sits down immediately and begins calculating the return trajectory "
                "using the Moon's gravity as a slingshot — the same backup method she had developed years earlier. "
                "The student works alongside her, handing papers, checking figures. "
                "Write this with the weight of three lives pressing down on every single calculation."
            )
        }
    ]
}


# ============================================================
# FUNÇÕES PÚBLICAS
# ============================================================

def _steps_ideais(cena: dict) -> list:
    """step_ideal pode ser um id ou uma lista de ids."""
    ideal = cena.get("step_ideal", [])
    return [ideal] if isinstance(ideal, str) else list(ideal)


def sortear_cena_canonica(skill: str, session_id: str, steps_sessao: list | None = None) -> dict | None:
    """
    Sorteia UMA cena canônica de forma determinística por sessão.
    O mesmo session_id sempre retorna a mesma cena para o mesmo personagem,
    mas sessões diferentes terão cenas diferentes.

    Como os marcos de cada sessão são sorteados, só concorrem as cenas cujo
    step ideal existe nesta sessão (senão a cena sorteada poderia nunca acontecer).

    Args:
        skill:        Skill da história (ex: "katherine_johnson").
        session_id:   ID único da sessão.
        steps_sessao: IDs das cenas desta sessão, em ordem (opcional).

    Returns:
        Dicionário da cena canônica, ou None se não houver cenas possíveis.
    """
    cenas = CENAS_CANONICAS.get(skill, [])
    if steps_sessao is not None:
        cenas = [c for c in cenas if set(_steps_ideais(c)) & set(steps_sessao)]
    if not cenas:
        return None

    # Hash MD5 do session_id garante distribuição uniforme e determinismo
    h = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
    idx = h % len(cenas)
    return cenas[idx]


def obter_instrucao_canonica(skill: str, session_id: str, step_atual: str, steps_sessao: list | None = None) -> str:
    """
    Retorna a instrução de prompt da cena canônica APENAS se o step atual
    é o step ideal para aquela cena (o primeiro deles, se a sessão tiver vários).

    Args:
        skill:        Skill da história.
        session_id:   ID da sessão.
        step_atual:   ID do step sendo processado agora.
        steps_sessao: IDs das cenas desta sessão, em ordem (opcional).

    Returns:
        String de instrução para injetar no prompt, ou string vazia.
    """
    cena = sortear_cena_canonica(skill, session_id, steps_sessao)
    if not cena:
        return ""

    ideais = _steps_ideais(cena)
    if steps_sessao is not None:
        ideais = [s for s in steps_sessao if s in ideais][:1]   # acontece uma vez só
    if step_atual in ideais:
        print(f"✨ Cena Canônica ATIVADA: [{cena['id']}] no step [{step_atual}]")
        return cena["instrucao_prompt"]

    return ""


def obter_id_cena_sorteada(skill: str, session_id: str, steps_sessao: list | None = None) -> str:
    """Retorna o ID da cena canônica sorteada (para logging)."""
    cena = sortear_cena_canonica(skill, session_id, steps_sessao)
    return cena["id"] if cena else "nenhuma"
