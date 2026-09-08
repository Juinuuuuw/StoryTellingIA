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
    "alan_turing": {
        "npc_global_visual": "1man, young Alan Turing, 20s, youthful boyish face, athletic build, bright blue eyes, unruly messy dark hair, wearing a rumpled academic tweed jacket, white shirt without a tie, focused and intelligent expression",
        "scenery_guideline": "Focus on 1930s Cambridge aesthetics merged with archaic, primitive experimental computing hardware. Emphasize massive, chaotic electromechanical prototypes with glowing vacuum tubes (glass valves), thick messy bundles of cables, clicking relays, infinite paper tape concepts, chalkboards overflowing with complex logic symbols, heavy dark wood university desks, and warm vintage lighting. The technology must look distinctly pre-silicon, showcasing the raw, analog electrical era.",
        "steps": [
            {
                "id": "cambridge_1936",
                "npc_principal": "Alan Turing",
                "goal": "Introduce the student as Turing's colleague at Cambridge. Present the challenge of 'unsolvable' mathematical problems.",
                "historical_facts": "In 1936, Alan Turing was a fellow at King's College, Cambridge. He was working on the 'Entscheidungsproblem' (Decision Problem), which asked if there is an algorithm that can decide if a mathematical statement is provable.",
                "emotion": "introspective",
                "cannot_happen": "modern electronic computers, internet",
                "must_happen": "Turing asks: 'Como podemos definir o que é computável?', choices about logic or physical steps"
            },
            {
                "id": "fita_infinita",
                "npc_principal": "Alan Turing",
                "goal": "Conceptualize the Turing Machine components: an infinite tape and a read/write head.",
                "historical_facts": "Turing's machine was a conceptual model. It consisted of an infinite tape divided into squares, a head that can read/write symbols, a state register, and a table of instructions. This simple model can simulate any computer algorithm.",
                "emotion": "focused",
                "cannot_happen": "silicon chips, screens",
                "must_happen": "Turing explains the tape: 'Pense em uma fita sem fim...', choices about reading symbols or moving the head"
            },
            {
                "id": "maquina_universal",
                "npc_principal": "Alan Turing",
                "goal": "Understand that one machine can be programmed to perform any task (The Universal Machine).",
                "historical_facts": "Turing proved that a 'Universal Machine' could simulate any other Turing machine. This is the origin of the stored-program computer: a machine where the instructions (software) are data stored in the same way as the information it processes.",
                "emotion": "amazement",
                "cannot_happen": "hard-wired machines only",
                "must_happen": "Turing realizes: 'Uma única máquina para tudo!', choices about changing instructions or changing hardware"
            },
            {
                "id": "enigma_bletchley",
                "npc_principal": "Alan Turing",
                "goal": "Introduce the Enigma codebreaking during WWII at Bletchley Park.",
                "historical_facts": "During WWII, Turing worked at Bletchley Park, building the Bombe machine to decipher the German Enigma codes, saving millions of lives and proving the practical power of early computing machines.",
                "emotion": "urgent",
                "cannot_happen": "internet, modern decryption",
                "must_happen": "Turing looks at the rotors: 'Cada segundo conta para quebrar o código!', choices about adjusting the rotors or analyzing the intercepted messages"
            },
            {
                "id": "legado_turing",
                "npc_principal": "Alan Turing",
                "goal": "Conclude with the legacy of Turing's 1936 paper as the foundation of Computer Science.",
                "historical_facts": "Turing's 1936 paper 'On Computable Numbers' is considered the founding document of Computer Science. He later worked on AI (The Turing Test) and codebreaking during WWII, but the 1936 machine remains his most profound conceptual gift.",
                "emotion": "triumphant",
                "cannot_happen": "forgetting his impact",
                "must_happen": "A vision of the future computers, warm goodbye"
            }
        ]
    },
    "historia_computacao": {
        "scenery_guideline": "Ensure each era feels distinct but shares a high-quality 'ToonYou' 3D aesthetic. 1830s London should be foggy with gaslight and brass machinery; 1930s Cambridge should have dark wood, glowing vacuum tubes (glass valves), messy cables, clicking relays, and archaic electromechanical prototypes; 1960s NASA should have bright offices, punch cards, and large mainframe shadows.",
        "steps": [
            {
                "id": "maquina_analitica",
                "npc_principal": "Charles Babbage",
                "npc_visual": "1man, elderly Charles Babbage, 19th century suit, messy grey hair, intelligent eyes, holding blueprints, steampunk era clothing",
                "goal": "Introduce the student as Babbage's assistant in 1837 London. Present the problem of mathematical errors in maritime tables.",
                "historical_facts": "Charles Babbage noticed that human 'computers' made many errors in mathematical tables used for navigation. The Analytical Engine included a 'Store' (memory), a 'Mill' (processor), and used punch cards inspired by Jacquard looms.",
                "emotion": "frustration",
                "cannot_happen": "modern technology, robots",
                "must_happen": "Babbage asks: 'Como podemos reduzir esses erros?', choices about building a machine or hiring people"
            },
            {
                "id": "ada_lovelace",
                "npc_principal": "Ada Lovelace",
                "npc_visual": "1woman, young Ada Lovelace, Victorian era dress, dark braided hair, elegant, aristocratic, highly intelligent expression",
                "goal": "The student is a researcher analyzing the Analytical Engine project with Ada Lovelace. She proposes the idea of sequences of instructions.",
                "historical_facts": "Ada Lovelace translated Luigi Menabrea's memoir on the machine and added her own 'Notes'. In 'Note G', she wrote the first algorithm intended for a machine: a method to calculate Bernoulli numbers.",
                "emotion": "inspiration",
                "cannot_happen": "purely numerical focus without question",
                "must_happen": "Ada asks: 'O que acha?', choices about step-by-step instructions or numerical limits"
            },
            {
                "id": "turing_legacy",
                "npc_principal": "Alan Turing",
                "npc_visual": "1man, young Alan Turing, 20s, youthful boyish face, athletic build, bright blue eyes, unruly messy dark hair, wearing a rumpled academic tweed jacket, white shirt without a tie, focused and intelligent expression",
                "goal": "Cambridge, 1936. Student is with Alan Turing. He's tackling computability.",
                "historical_facts": "In his paper 'On Computable Numbers', Turing introduced the concept of a Universal Machine. He proved that some problems (like the Halting Problem) are undecidable, defining the limits of what computers can do.",
                "emotion": "contemplation",
                "cannot_happen": "computers already existing",
                "must_happen": "Turing asks: 'Como saber se um problema pode ser resolvido por uma máquina?', choices about symbols on a tape or traditional proof"
            },
            {
                "id": "arpanet",
                "npc_principal": "J.C.R. Licklider",
                "npc_visual": "1man, J.C.R. Licklider, 1960s, middle-aged, wearing a neat suit and tie, thick glasses, professional scientist look",
                "goal": "Student is an engineer in the ARPANET project. Discussion about network failure and university connection.",
                "historical_facts": "ARPANET was the first network to implement TCP/IP and packet switching. The first message was sent between UCLA and SRI in 1969. The message was supposed to be 'LOGIN', but the system crashed after 'LO'.",
                "emotion": "urgency",
                "cannot_happen": "internet already existing",
                "must_happen": "Scientists ask for opinion on connection failure, choices about packets or exclusive connections"
            }
        ]
    },

    "katherine_johnson": {
        "npc_global_visual": "1woman, ebony skin, dark brown skin, short curly black hair, wearing a 1950s professional beige dress with a white collar, cat-eye glasses, intelligent expression",
        "steps": [
            {
                "id": "west_computing",
                "npc_principal": "Katherine Johnson",
                "goal": "Introduce Katherine as a 'Human Computer' at NASA Langley during the era of segregation.",
                "historical_facts": "Katherine Johnson worked at the West Area Computing unit at NASA. In the 1950s, human computers—mostly women—performed complex mathematical calculations by hand. Despite segregation, her brilliance made her indispensable.",
                "emotion": "determination",
                "cannot_happen": "modern electronic calculators, complete equality",
                "must_happen": "Katherine is working on data: 'Os números não mentem', choices about double-checking or asking for more data"
            },
            {
                "id": "mercury_shepard",
                "npc_principal": "Katherine Johnson",
                "goal": "Calculate the trajectory for Alan Shepard's first suborbital flight (1961).",
                "historical_facts": "Katherine calculated the trajectory for Freedom 7, the flight that made Alan Shepard the first American in space. She mapped the path from launch to landing, ensuring he would be recovered safely in the ocean.",
                "emotion": "concentration",
                "cannot_happen": "satellite GPS",
                "must_happen": "Katherine checks the parabolic path: 'Temos que acertar o alvo!', choices about launch angle or timing"
            },
            {
                "id": "john_glenn_request",
                "npc_principal": "Katherine Johnson",
                "goal": "The iconic moment when John Glenn asked for her specifically to verify the orbital calculations.",
                "historical_facts": "Before his orbital flight in 1962, John Glenn was wary of the new IBM computers. He famously said, 'Get the girl to check the numbers. If she says they’re good, then I’m ready to go.' Katherine spent days verifying them by hand.",
                "emotion": "respect",
                "cannot_happen": "the computer being trusted blindly",
                "must_happen": "The call comes in: 'O Glenn quer você!', choices about checking the IBM output or starting from scratch"
            },

            {
                "id": "apollo_13_resgate",
                "npc_principal": "Katherine Johnson",
                "goal": "Working on the Apollo 13 emergency return trajectory.",
                "historical_facts": "When the Apollo 13 mission was aborted in 1970 due to an explosion, Katherine Johnson's backup procedures and charts were used to calculate a safe return path for the crew, bringing them home alive.",
                "emotion": "urgent",
                "cannot_happen": "astronauts getting lost in space",
                "must_happen": "Katherine races against time: 'Precisamos trazê-los de volta agora!', choices about the star alignment charts or the lunar module engine burn"
            },
            {
                "id": "legado_katherine",
                "npc_principal": "Katherine Johnson",
                "goal": "Reflect on her legacy as a pioneer in space exploration and civil rights.",
                "historical_facts": "Katherine Johnson worked at NASA for 33 years. She was awarded the Presidential Medal of Freedom in 2015. Her story, along with other Black female mathematicians, was told in 'Hidden Figures'. She passed away in 2020 at age 101.",
                "emotion": "gratitude",
                "cannot_happen": "remaining hidden",
                "must_happen": "A celebration of her life, Katherine says: 'Sempre conte com a matemática', warm ending"
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
