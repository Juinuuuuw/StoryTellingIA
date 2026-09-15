import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ESTADOS_DIR = os.path.join(BASE_DIR, "..", "historias", "estados")
os.makedirs(ESTADOS_DIR, exist_ok=True)

# ============================================================
# BLUEPRINTS NARRATIVOS (A ESTRUTURA REAL)
# ============================================================
BLUEPRINTS = {
    # ── ALAN TURING ──────────────────────────────────────────────────────────
    # 3 atos: Início (Cambridge + Máquina de Turing), Desenvolvimento
    # (Máquina Universal + Bletchley Park), Fim (Legado)
    "alan_turing": {
        "npc_global_visual": "1man, Alan Turing, thin angular face, high cheekbones, pale blue eyes, short wavy brown hair slightly disheveled, clean-shaven, slender build, wearing a rumpled brown tweed jacket over a white dress shirt with collar slightly open, no tie, no hat, NOT wearing glasses, 1940s British academic style, intelligent focused expression",
        "scenery_guideline": "Era: 1930s-1940s wartime Britain. Key locations: Bletchley Park stone mansion, King's College Cambridge gothic arches. Key objects: the Bombe electromechanical decryption machine (large bronze-and-steel cabinet with rows of spinning rotors and clicking relays), Enigma cipher machine (compact wooden box with keyboard and rotating letter wheels), chalk-covered blackboards dense with logic symbols and mathematical proofs, rolls of paper tape, vacuum tubes (glass valves) glowing warm amber, heavy dark oak desks under incandescent bulbs, dusty stone corridors, WWII-era military maps pinned to the walls, teacups, handwritten notebooks. Atmosphere: grey overcast British sky through tall narrow windows, dim warm tungsten lighting, secrecy and urgent wartime pressure.",
        "steps": [
            {
                "id": "cambridge_maquina",
                "npc_principal": "Alan Turing",
                "goal": "Introduce the student as Turing's colleague at Cambridge in 1936. Present the Entscheidungsproblem and the birth of the Turing Machine: an infinite tape, a read/write head, and simple state rules that can compute anything.",
                "historical_facts": "In 1936, Turing was a fellow at King's College, Cambridge, working on the 'Entscheidungsproblem'. His answer was a thought-experiment machine: an infinite tape divided into squares, a head that reads/writes symbols, a state register, and an instruction table. This simple model proved it could simulate ANY algorithm — the conceptual birth of every computer ever built.",
                "emotion": "introspective",
                "cannot_happen": "modern electronic computers, internet, silicon chips",
                "must_happen": "Turing unveils the tape metaphor: 'Pense em uma fita sem fim, cada quadrado guarda um símbolo — e essa ideia simples resolve o impossível.' Choices about logic or moving the tape head"
            },
            {
                "id": "universal_enigma",
                "npc_principal": "Alan Turing",
                "goal": "Show that one Universal Machine can run any program (stored-program concept) AND that Turing's ideas became real at Bletchley Park breaking Enigma codes during WWII.",
                "historical_facts": "Turing proved a Universal Machine could simulate any Turing Machine — the origin of stored-program computers. During WWII he applied this at Bletchley Park, building the electromechanical Bombe to crack German Enigma ciphers, shortening the war by an estimated 2–4 years and saving millions of lives.",
                "emotion": "urgent",
                "cannot_happen": "internet, modern decryption software, silicon chips",
                "must_happen": "Turing shows the Bombe's spinning rotors: 'Uma única máquina para tudo — e agora ela vai quebrar o código inquebrável.' Choices about adjusting rotors or analyzing intercepted messages"
            },
            {
                "id": "legado_turing",
                "npc_principal": "Alan Turing",
                "goal": "Conclude with Turing's enduring legacy: the 1936 paper as the foundation of Computer Science, the Turing Test, and his tragic but ultimately honoured fate.",
                "historical_facts": "Turing's 1936 paper 'On Computable Numbers' is the founding document of Computer Science. He later proposed the Turing Test for machine intelligence (1950). Despite being chemically castrated by the British government for his homosexuality, he was posthumously pardoned in 2013 and his face graced the £50 note in 2021.",
                "emotion": "triumphant",
                "cannot_happen": "forgetting his impact, a purely happy uncritical ending",
                "must_happen": "A bittersweet vision of the digital future Turing made possible; warm, meaningful farewell"
            }
        ]
    },

    # ── HISTÓRIA DA COMPUTAÇÃO ───────────────────────────────────────────────
    # 3 atos: Início (Babbage + Ada), Desenvolvimento (Turing 1936),
    # Fim (ARPANET — nascimento da internet)
    "historia_computacao": {
        "scenery_guideline": "Ensure each era feels distinct but shares a high-quality anime 2D aesthetic. 1830s London: foggy streets, gaslight, brass gears, ink blueprints. 1930s Cambridge: dark wood, glowing vacuum tubes, messy cables, clicking relays. 1960s ARPANET lab: bright fluorescent offices, punch cards, massive mainframe towers.",
        "steps": [
            {
                "id": "babbage_ada",
                "npc_principal": "Ada Lovelace",
                "npc_visual": "1woman, young Ada Lovelace, Victorian era dress, dark braided hair, elegant, aristocratic, highly intelligent expression",
                "goal": "1837 London. The student joins Charles Babbage and Ada Lovelace. Babbage dreams of a machine that eliminates human calculation errors; Ada sees further — she writes the first algorithm intended for a machine (Bernoulli numbers in 'Note G').",
                "historical_facts": "Babbage noticed maritime tables full of human errors and designed the Analytical Engine with a 'Store' (memory) and 'Mill' (processor), using punch cards inspired by Jacquard looms. Ada Lovelace translated Menabrea's memoir and added her own Notes, including 'Note G' — the world's first published algorithm, calculating Bernoulli numbers.",
                "emotion": "inspiration",
                "cannot_happen": "modern technology, electronic computers, internet",
                "must_happen": "Ada hands the student her Note G manuscript: 'A máquina não apenas calcula — ela pode executar qualquer sequência de operações que pudermos imaginar.' Choices about step-by-step instructions or the machine's numerical limits"
            },
            {
                "id": "turing_computabilidade",
                "npc_principal": "Alan Turing",
                "npc_visual": "1man, young Alan Turing, 20s, youthful boyish face, athletic build, bright blue eyes, unruly messy dark hair, wearing a rumpled academic tweed jacket, white shirt without a tie, focused and intelligent expression",
                "goal": "Cambridge, 1936. Student works alongside Turing as he formalises what it means for a problem to be 'computable', inventing the Universal Machine concept and identifying the Halting Problem — the first proof of a fundamental limit of computation.",
                "historical_facts": "In 'On Computable Numbers' (1936), Turing defined computability with his thought-experiment machine and proved that some problems are undecidable — no algorithm can ever solve them. The Halting Problem is the most famous example. This paper is the conceptual blueprint for every digital computer.",
                "emotion": "contemplation",
                "cannot_happen": "computers already built and running, internet",
                "must_happen": "Turing draws a tape on the chalkboard: 'Como saber se um problema pode ser resolvido por uma máquina? Talvez alguns nunca possam.' Choices about symbols on the tape or a traditional mathematical proof"
            },
            {
                "id": "arpanet_nascimento",
                "npc_principal": "J.C.R. Licklider",
                "npc_visual": "1man, J.C.R. Licklider, 1960s, middle-aged, wearing a neat suit and tie, thick glasses, professional scientist look",
                "goal": "1969, ARPANET lab. The student is an engineer as the first inter-university message is sent — and spectacularly crashes after two letters, 'LO', inadvertently becoming the internet's first word.",
                "historical_facts": "ARPANET was the US Defense Department's network using packet-switching — data split into packets routed independently. On Oct 29 1969, Charley Kline at UCLA tried to send 'LOGIN' to SRI. The system crashed after 'L' and 'O'. Those two letters, 'LO', became the internet's accidental first message.",
                "emotion": "urgency",
                "cannot_happen": "internet already existing, modern web browsers",
                "must_happen": "The terminal shows only 'LO' before crashing; Licklider grins: 'Dois caracteres. O começo de tudo.' Choices about diagnosing the packet failure or celebrating the historic connection"
            }
        ]
    },

    # ── KATHERINE JOHNSON ────────────────────────────────────────────────────
    # 3 atos: Início (West Computing + segregação), Desenvolvimento
    # (Shepard + Glenn), Fim (Apollo 13 + Legado)
    "katherine_johnson": {
        "npc_global_visual": "1woman, Katherine Johnson, dark brown skin, ebony complexion, short tightly curled black hair, wearing a 1950s professional beige pencil skirt suit with white collar, pearl earrings, cat-eye glasses with dark frames, holding a mechanical pencil, calm confident intelligent expression, NOT wearing lab coat",
        "scenery_guideline": "Era: 1950s-1970s NASA Langley Research Center and Mission Control, Hampton Virginia. Key locations: West Area Computing bullpen (large open office with rows of desks), Mission Control Houston (banks of flickering monitors and consoles with rows of men in white shirts and thin ties), rocket launch viewing areas. Key objects: IBM 7090 mainframe computer (enormous room-filling metal cabinet with blinking lights and reel-to-reel tape drives), mechanical Friden calculators (heavy chrome desktop adding machines), hand-ruled trajectory charts on large graph paper, manila folders stuffed with calculations, chalkboards with orbital equations and velocity vectors, rotary telephones, American flag, NASA logo placard, 1960s fluorescent office lighting, clip-on security badges. Signs visible: 'COLORED COMPUTERS' and 'WHITE COMPUTERS' (segregation era). Atmosphere: fluorescent lit 1950s government office, optimistic Space Race energy mixed with racial tension, black-and-white NASA mission photography on walls.",
        "steps": [
            {
                "id": "west_computing_inicio",
                "npc_principal": "Katherine Johnson",
                "goal": "Introduce Katherine as a 'Human Computer' at NASA Langley in the 1950s. Show the injustice of segregation — separate bathrooms, coffee pots labelled 'Coloured' — AND her mathematical brilliance that made her indispensable, culminating in her calculating Alan Shepard's suborbital trajectory.",
                "historical_facts": "Katherine Johnson worked at the West Area Computing unit — a segregated division of NASA Langley. Despite laws forcing her to use separate facilities, her mastery of analytic geometry made her irreplaceable. In 1961 she calculated the precise trajectory for Freedom 7, making Alan Shepard the first American in space, mapping the parabolic path from launch to ocean recovery.",
                "emotion": "determination",
                "cannot_happen": "modern electronic calculators, satellite GPS, complete racial equality",
                "must_happen": "Katherine, surrounded by segregated 'Coloured' signs, taps her pencil on a trajectory sheet: 'Os números não mentem — e a matemática não conhece cor.' Choices about double-checking the parabolic path or confronting an unjust rule"
            },
            {
                "id": "glenn_orbital",
                "npc_principal": "Katherine Johnson",
                "goal": "The iconic 1962 moment: John Glenn refuses to launch unless Katherine Johnson personally verifies the IBM computer's orbital calculations by hand.",
                "historical_facts": "Before his Friendship 7 orbital flight (Feb 20, 1962), astronaut John Glenn distrusted the new IBM 7090 computers. He told NASA engineers: 'Get the girl to check the numbers. If she says they're good, then I'm ready to go.' Katherine spent a day and a half verifying every number by hand. Glenn launched. The mission succeeded.",
                "emotion": "respect",
                "cannot_happen": "the computer being trusted blindly, modern GPS",
                "must_happen": "A NASA engineer bursts in: 'Glenn quer você, Katherine — se você disser que os números estão certos, ele vai.' Choices about verifying the IBM output from scratch or trusting the machine"
            },
            {
                "id": "apollo_legado",
                "npc_principal": "Katherine Johnson",
                "goal": "Apollo 13 emergency (1970): Katherine's backup star-chart procedures help bring the crew home. Conclude with her legacy — 33 years at NASA, Presidential Medal of Freedom (2015), Hidden Figures (2016), passing at 101 in 2020.",
                "historical_facts": "After the Apollo 13 oxygen tank exploded on April 13, 1970, ground controllers used Katherine Johnson's backup navigation procedures and star-alignment charts to calculate a safe return trajectory using the Lunar Module as a lifeboat. The crew splashed down safely on April 17. In 2015 Obama awarded her the Presidential Medal of Freedom. She passed away February 24, 2020, aged 101.",
                "emotion": "gratitude",
                "cannot_happen": "astronauts dying, remaining historically hidden",
                "must_happen": "Katherine calmly hands over her backup star charts as alarms blare: 'Precisamos trazê-los de volta — e os números vão mostrar o caminho.' Warm, earned farewell celebrating her full legacy"
            }
        ]
    }
}

class StateManager:
    def __init__(self):
        self.sessions = {}

    def create_session(self, student_name, focus_skill, theme):
        session_id = str(datetime.now().timestamp()).replace(".", "")
        
        # Fallback robusto: tenta a skill pedida, senão pega a primeira disponível
        blueprint = BLUEPRINTS.get(focus_skill)
        if not blueprint:
            first_key = list(BLUEPRINTS.keys())[0]
            blueprint = BLUEPRINTS[first_key]
        
        state = {
            "session_id": session_id,
            "student": {
                "name": student_name,
                "focus_skill": focus_skill,
                "theme": theme
            },
            "current_step_idx": 0,
            "blueprint": blueprint,
            "history": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_update": datetime.now().isoformat()
            }
        }
        
        self.sessions[session_id] = state
        self.save_state(session_id)
        return session_id

    def advance_state(self, session_id, choice_text):
        state = self.load_state(session_id)
        if not state:
            return None
        narrative = state.get("last_narrative", "")
        idx = state["current_step_idx"]
        step = state["blueprint"]["steps"][idx]

        # Calcula o ato atual para salvar no histórico
        total = len(state["blueprint"]["steps"])
        if idx >= total * 0.66:
            ato_atual = 3
        elif idx >= total * 0.33:
            ato_atual = 2
        else:
            ato_atual = 1

        state["history"].append({
            "choice": choice_text,
            "step": step["id"],
            "ato": ato_atual,
            "emotion": step.get("emotion", ""),
            "narrative": narrative
        })
        state["current_step_idx"] += 1
        state["metadata"]["last_update"] = datetime.now().isoformat()

        self.sessions[session_id] = state
        self.save_state(session_id)
        return state

    def get_current_context(self, session_id):
        state = self.load_state(session_id)
        if not state:
            return None

        idx = state["current_step_idx"]
        total = len(state["blueprint"]["steps"])
        if idx >= total:
            return None

        step = state["blueprint"]["steps"][idx]

        # Calcula o ato narrativo dinamicamente pela posição relativa do step
        if idx >= total * 0.66:
            ato = 3
        elif idx >= total * 0.33:
            ato = 2
        else:
            ato = 1

        return {
            "student_name": state["student"]["name"],
            "student_genero": state["student"].get("genero", "Masculino"),
            "theme": state["student"]["theme"],
            "current_step": step["id"],
            "skill": state["student"].get("focus_skill", ""),
            "npc_principal": step.get("npc_principal", ""),
            "npc_visual": step.get("npc_visual", state["blueprint"].get("npc_global_visual", "")),
            "scenery_guideline": state["blueprint"].get("scenery_guideline", ""),
            "goal": step["goal"],
            "historical_facts": step.get("historical_facts", ""),
            "emotion": step["emotion"],
            "cannot_happen": step["cannot_happen"],
            "must_happen": step["must_happen"],
            "is_final": idx == total - 1,
            "ato": ato,
            "step_index": idx,
            "total_steps": total
        }

    def save_state(self, session_id):
        state = self.sessions.get(session_id)
        if not state:
            return
            
        file_path = os.path.join(ESTADOS_DIR, f"sessao_{session_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def load_state(self, session_id):
        # Primeiro tenta na memória
        if session_id in self.sessions:
            return self.sessions[session_id]
            
        # Depois no disco
        file_path = os.path.join(ESTADOS_DIR, f"sessao_{session_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                state = json.load(f)
                self.sessions[session_id] = state
                return state
        return None

# Instância global
manager = StateManager()
