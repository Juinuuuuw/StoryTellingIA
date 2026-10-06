import json
import os
import random
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ESTADOS_DIR = os.path.join(BASE_DIR, "..", "historias", "estados")
os.makedirs(ESTADOS_DIR, exist_ok=True)

# ============================================================
# BLUEPRINTS NARRATIVOS (A ESTRUTURA REAL)
# ============================================================
# Cada história tem um banco de 6 marcos históricos (em ordem cronológica).
# Ao criar a sessão, sorteamos 2 marcos e montamos 5 cenas:
#
#   1. preparação do marco A   → o mundo antes do marco (abre a história)
#   2. ★ marco A               → o momento histórico acontecendo
#   3. preparação do marco B   → salto no tempo até a véspera do marco B
#   4. ★ marco B
#   5. final                   → legado e despedida
#
# Campos de um marco: id, ano, titulo, evento (PT-BR — vão para a tela, o prompt e o quiz),
# "preparacao" e "momento" (o step de cada cena). npc_principal / npc_visual /
# scenery_guideline são opcionais e sobrepõem os da história.
MARCOS_POR_HISTORIA = 2

_TURING_POS_GUERRA = "Era: 1945-1953 postwar Britain. Key locations: National Physical Laboratory in Teddington, the University of Manchester computing laboratory, Turing's small cluttered study. Key objects: tall grey metal racks of the Manchester Mark 1 computer full of glowing vacuum tubes, round cathode-ray tube memory screens with grids of glowing dots, teleprinter with punched paper tape, wooden chessboard, blackboards with equations, piles of handwritten notes, sunflowers and pine cones on the desk. Atmosphere: grey rainy northern English light through tall windows, humming machines, quiet postwar austerity."

BLUEPRINTS = {
    # ── ALAN TURING ──────────────────────────────────────────────────────────
    "alan_turing": {
        # Nomes/termos desta história — usados para barrar mistura com as outras (ver termos_proibidos)
        "termos_exclusivos": ["Turing", "Cambridge", "King's College", "Bombe", "Enigma", "Bletchley", "Hut 8", "U-boat", "Banburismus", "Turochamp", "Champernowne", "Teddington", "Manchester", "rotores", "rotor", "fita infinita", "fita sem fim"],
        "npc_principal": "Alan Turing",
        "npc_global_visual": "1man, Alan Turing, thin angular face, high cheekbones, pale blue eyes, short wavy brown hair slightly disheveled, clean-shaven, slender build, wearing a rumpled brown tweed jacket over a white dress shirt with collar slightly open, no tie, no hat, NOT wearing glasses, 1940s British academic style, intelligent focused expression",
        "scenery_guideline": "Era: 1930s-1940s wartime Britain. Key locations: Bletchley Park stone mansion, King's College Cambridge gothic arches. Key objects: the Bombe electromechanical decryption machine (large bronze-and-steel cabinet with rows of spinning rotors and clicking relays), Enigma cipher machine (compact wooden box with keyboard and rotating letter wheels), chalk-covered blackboards dense with logic symbols and mathematical proofs, rolls of paper tape, vacuum tubes (glass valves) glowing warm amber, heavy dark oak desks under incandescent bulbs, dusty stone corridors, WWII-era military maps pinned to the walls, teacups, handwritten notebooks. Atmosphere: grey overcast British sky through tall narrow windows, dim warm tungsten lighting, secrecy and urgent wartime pressure.",
        "marcos": [
            {
                "id": "maquina_turing",
                "ano": "1936",
                "titulo": "A Máquina de Turing",
                "evento": "Turing conclui o artigo 'On Computable Numbers' (1936) e descreve uma máquina imaginária — uma fita sem fim, uma cabeça que lê e escreve símbolos e uma tabela de regras — capaz de executar qualquer cálculo. Na mesma ideia nasce a Máquina Universal: uma única máquina que imita qualquer outra lendo as instruções na própria fita. É o projeto teórico de todo computador moderno.",
                "preparacao": {
                    "epoca": "King's College, Cambridge, 1935-1936",
                    "goal": "The student becomes Turing's young research assistant at King's College. Present Turing as an eccentric, brilliant and very human figure (he runs long distances, talks fast when excited) and the challenge that obsesses him: Hilbert's Entscheidungsproblem — can a mechanical procedure decide whether ANY mathematical statement is provable?",
                    "historical_facts": "In 1935, 23-year-old Alan Turing, a fellow of King's College, Cambridge, heard about David Hilbert's Entscheidungsproblem (the 'decision problem') in Max Newman's lectures: is there a mechanical method that decides, for any mathematical statement, whether it can be proved? Turing reportedly had his key insight while resting in a meadow at Grantchester after a long run.",
                    "emotion": "curiosity",
                    "cannot_happen": "electronic computers, the Turing Machine already finished, World War II already started",
                    "must_happen": "Turing poses the challenge to the student: 'Será que existe um método mecânico capaz de decidir qualquer problema da matemática?' Choices about how to start attacking the problem"
                },
                "momento": {
                    "epoca": "King's College, Cambridge, 1936",
                    "goal": "The student is beside Turing as he finishes 'On Computable Numbers' and explains the Turing Machine (infinite tape, read/write head, table of rules) and the Universal Machine: one single machine that can imitate any other by reading its instructions from the tape — the idea of software.",
                    "historical_facts": "Turing submitted 'On Computable Numbers, with an Application to the Entscheidungsproblem' on 28 May 1936. The paper described a machine with an infinite paper tape divided into squares, a head that reads, writes or erases one symbol at a time, and a finite table of rules. He showed that a Universal Machine could simulate any other such machine, and proved that some problems (like the Halting Problem) can never be solved by any algorithm — answering Hilbert with a 'no'.",
                    "emotion": "wonder",
                    "cannot_happen": "a physical computer being built, World War II, silicon chips",
                    "must_happen": "Turing unveils the tape metaphor: 'Pense em uma fita sem fim, cada quadrado guarda um símbolo — e essa ideia simples resolve o impossível.' Choices about writing symbols on the tape or testing the Universal Machine idea"
                }
            },
            {
                "id": "bombe_victory",
                "ano": "1940",
                "titulo": "A Bombe 'Victory' Começa a Funcionar",
                "evento": "Em março de 1940 a primeira Bombe britânica, apelidada de 'Victory', começa a funcionar em Bletchley Park. Projetada por Turing a partir da 'bomba' dos matemáticos poloneses, a máquina testa milhares de posições dos rotores do Enigma por conta própria — é a primeira vez que uma máquina ajuda a quebrar códigos em grande escala.",
                "preparacao": {
                    "epoca": "Bletchley Park, setembro de 1939",
                    "goal": "The war has just begun. Turing and the student arrive at the secret codebreaking centre of Bletchley Park and face the German Enigma: billions of billions of settings that change every midnight. Turing sketches the idea of a machine to fight a machine. Nothing works yet.",
                    "historical_facts": "On 4 September 1939, the day after Britain declared war, Turing reported to the Government Code and Cypher School at Bletchley Park. The Enigma machine could be set in about 158 quintillion ways, and German operators changed the settings every midnight. Polish mathematicians had already built an electromechanical 'bomba' and shared their work with the British in July 1939.",
                    "emotion": "urgency",
                    "cannot_happen": "the Bombe already working, the code already broken, modern computers",
                    "must_happen": "Turing spins the rotors of a captured Enigma: 'Precisamos de uma máquina para vencer outra máquina.' Choices about studying the Polish notes or looking for repeated words in intercepted messages"
                },
                "momento": {
                    "epoca": "Bletchley Park, março de 1940",
                    "goal": "The first British Bombe, 'Victory', is switched on for the first time. The student watches the huge bronze cabinet come alive, its drums spinning and relays clicking as it tests rotor positions faster than any team of people could.",
                    "historical_facts": "The first Bombe, built by the British Tabulating Machine Company from Turing's design and nicknamed 'Victory', was installed at Bletchley Park on 18 March 1940. It had 36 sets of rotating drums imitating Enigma rotors and used 'cribs' — guessed words like weather reports — to eliminate impossible settings. Gordon Welchman's 'diagonal board' soon made it much faster.",
                    "emotion": "awe",
                    "cannot_happen": "the naval code already broken, public celebration, modern computers",
                    "must_happen": "The Bombe roars to life with hundreds of clicking relays; Turing: 'Ela pensa mais rápido do que cem de nós juntos.' Choices about feeding the machine a guessed word or checking the first result by hand"
                }
            },
            {
                "id": "enigma_naval",
                "ano": "1941",
                "titulo": "A Quebra do Código Enigma",
                "evento": "Em 1941 a equipe de Turing no Hut 8 de Bletchley Park quebra o Enigma da Marinha alemã. Os Aliados passam a ler as mensagens dos submarinos U-boat e desviam os comboios do perigo. Historiadores estimam que isso encurtou a Segunda Guerra Mundial em cerca de dois anos e salvou milhões de vidas — mas tudo ficou em segredo por 30 anos.",
                "preparacao": {
                    "epoca": "Hut 8, Bletchley Park, início de 1941",
                    "goal": "German U-boats are sinking Allied supply ships in the Atlantic and the naval Enigma still resists. The student shares long nights in Hut 8 with an exhausted Turing, who sometimes sleeps beside the Bombe. Show failure and pressure — the code is NOT broken yet.",
                    "historical_facts": "The German Navy used a more complex version of Enigma. In early 1941, U-boat 'wolf packs' were sinking hundreds of thousands of tons of Allied shipping every month. Turing led Hut 8 and invented 'Banburismus', a statistical method to cut down the settings the Bombes had to test. Turing sometimes worked through the night beside the clicking machines.",
                    "emotion": "tension",
                    "cannot_happen": "the naval Enigma already broken, celebrations of victory, modern computers",
                    "must_happen": "A radio report of another sunk convoy reaches the hut; Turing: 'Cada noite que perdemos, um navio afunda.' Choices about trying Banburismus on the night's messages or waiting for captured codebooks"
                },
                "momento": {
                    "epoca": "Hut 8, Bletchley Park, 1941",
                    "goal": "The student witnesses the exact moment the Bombe stops, the first German naval message is decrypted letter by letter, and the team realises they can now read U-boat orders. The joy must stay silent: if the Germans find out, they will change the code.",
                    "historical_facts": "Combining the Bombes, Banburismus and codebooks captured from German ships (such as U-110 in May 1941), Hut 8 broke the naval Enigma in 1941. U-boat messages were read and Atlantic convoys were rerouted around the submarines; shipping losses fell sharply. The work stayed classified for about 30 years.",
                    "emotion": "triumph",
                    "cannot_happen": "public celebration, the Germans discovering the code was broken, modern computers",
                    "must_happen": "The Bombe suddenly stops; the decrypted German message appears letter by letter; Turing whispers: 'Conseguimos — mas ninguém lá fora pode saber.' Choices about warning the convoys or keeping the secret"
                }
            },
            {
                "id": "projeto_ace",
                "ano": "1946",
                "titulo": "O Projeto do Computador ACE",
                "evento": "Em fevereiro de 1946 Turing apresenta ao Laboratório Nacional de Física o projeto do ACE (Automatic Computing Engine): um dos primeiros projetos completos de um computador eletrônico que guarda o próprio programa na memória — como todos os computadores de hoje.",
                "scenery_guideline": _TURING_POS_GUERRA,
                "preparacao": {
                    "epoca": "Londres, 1945, logo após o fim da guerra",
                    "goal": "The war is over but Turing cannot tell anyone what he did. The student meets him as he is invited by the National Physical Laboratory to design a real electronic computer. Turing dreams of a machine that could hold its own program in memory; others think it is impossible.",
                    "historical_facts": "After the war, Bletchley Park's work was secret and Turing could not talk about it. In October 1945 he joined the National Physical Laboratory (NPL) in Teddington, London, to design an electronic computer. He wanted to turn his 1936 'Universal Machine' into a real machine using electronic valves (vacuum tubes) and a memory made of mercury delay lines.",
                    "emotion": "hope",
                    "cannot_happen": "the computer already built, transistors, modern computers",
                    "must_happen": "Turing sketches boxes and arrows on a blackboard: 'E se a máquina guardasse as próprias instruções na memória?' Choices about drawing the memory or calculating how many valves the machine would need"
                },
                "momento": {
                    "epoca": "Laboratório Nacional de Física, Teddington, fevereiro de 1946",
                    "goal": "Turing presents his finished design, the 'Proposed Electronic Calculator' — the ACE — to the NPL committee. The student helps him with the drawings as he explains a computer that stores its program in memory and can be reprogrammed for any task.",
                    "historical_facts": "On 19 February 1946 Turing presented his report 'Proposed Electronic Calculator' to the NPL executive committee: one of the first complete designs of a stored-program electronic computer. Bureaucracy delayed the project, but a smaller version, the Pilot ACE, ran in 1950 and was one of the fastest computers of its time.",
                    "emotion": "pride",
                    "cannot_happen": "transistors, personal computers, the full ACE being finished immediately",
                    "must_happen": "Turing lays the thick report on the committee table: 'Uma única máquina, e qualquer tarefa que pudermos descrever.' Choices about answering the committee's doubts or showing a sample program"
                }
            },
            {
                "id": "turochamp",
                "ano": "1948",
                "titulo": "O Primeiro Programa de Xadrez",
                "evento": "Em 1948 Turing e seu amigo David Champernowne escrevem o Turochamp, o primeiro programa de computador para jogar xadrez. Ainda não havia um computador capaz de rodá-lo — então, em 1952, o próprio Turing executou o programa à mão, fazendo os cálculos no papel, cerca de meia hora para cada jogada.",
                "scenery_guideline": _TURING_POS_GUERRA,
                "preparacao": {
                    "epoca": "Cambridge, 1948",
                    "goal": "Turing, on leave in Cambridge, is fascinated by a question: can a machine play chess? The student joins Turing and his friend David Champernowne on long walks and in a cluttered study full of chessboards, as they try to write down the rules a machine would need to 'think' about a move.",
                    "historical_facts": "Turing believed that playing chess was a good test of machine intelligence. In 1948 he and the economist David Champernowne started designing a set of rules a computer could follow to choose a chess move: count the pieces, value mobility, look a few moves ahead.",
                    "emotion": "playfulness",
                    "cannot_happen": "a computer already playing chess, modern chess engines, World War II",
                    "must_happen": "Turing moves a knight and freezes: 'Se eu consigo explicar por que fiz essa jogada, uma máquina também consegue.' Choices about writing the rule for capturing pieces or the rule for protecting the king"
                },
                "momento": {
                    "epoca": "Cambridge e Manchester, 1948",
                    "goal": "Turochamp is finished: the first computer chess program in history. With no machine powerful enough to run it, Turing becomes the computer himself, executing the program by hand on paper while the student plays against it.",
                    "historical_facts": "Turing and Champernowne completed Turochamp in 1948, the first known computer chess program. No computer of the time could run it, so in 1952 Turing executed the algorithm himself with pencil and paper in a game against his colleague Alick Glennie, taking about half an hour per move. The program lost, but it proved a machine could follow rules to play a whole game.",
                    "emotion": "excitement",
                    "cannot_happen": "a computer running the program, modern chess engines, the program winning easily",
                    "must_happen": "Turing scribbles calculations for minutes before moving a single pawn: 'Eu sou a máquina agora — e ela é bem lenta!' Choices about attacking the program's queen or testing it with a tricky move"
                }
            },
            {
                "id": "teste_turing",
                "ano": "1950",
                "titulo": "O Teste de Turing",
                "evento": "Em outubro de 1950 Turing publica o artigo 'Computing Machinery and Intelligence', que começa com a pergunta 'As máquinas podem pensar?'. Ele propõe o Jogo da Imitação, hoje chamado Teste de Turing: se uma pessoa conversando por escrito não conseguir distinguir a máquina de um humano, a máquina pode ser considerada inteligente. É o ponto de partida da inteligência artificial.",
                "scenery_guideline": _TURING_POS_GUERRA,
                "preparacao": {
                    "epoca": "Universidade de Manchester, 1949",
                    "goal": "Turing now works with the Manchester Mark 1, one of the first real stored-program computers. A public controversy erupts in the newspapers: some scientists say a machine can never think. The student helps Turing prepare his answer while the giant machine hums beside them.",
                    "historical_facts": "In 1948 Turing joined the University of Manchester, where the Manchester Mark 1 computer was running. In June 1949 a famous brain surgeon argued that no machine could ever equal a human mind. Turing answered in The Times: 'This is only a foretaste of what is to come, and only the shadow of what is going to be.'",
                    "emotion": "defiance",
                    "cannot_happen": "modern artificial intelligence, the internet, the paper already published",
                    "must_happen": "Turing reads the newspaper attack aloud and smiles: 'Isto é só uma prévia do que está por vir.' Choices about asking how to prove a machine can think or about testing the Mark 1 with a question"
                },
                "momento": {
                    "epoca": "Manchester, outubro de 1950",
                    "goal": "Turing's paper 'Computing Machinery and Intelligence' is published. The student plays the Imitation Game with him: hidden behind a teleprinter, can the student tell if the answers come from a person or a machine?",
                    "historical_facts": "In October 1950 the journal Mind published 'Computing Machinery and Intelligence', which opens with 'I propose to consider the question, Can machines think?'. Turing replaced the question with the Imitation Game, now called the Turing Test, and predicted that by the year 2000 machines would fool many people in short conversations.",
                    "emotion": "wonder",
                    "cannot_happen": "modern chatbots, the internet, robots walking around",
                    "must_happen": "A teleprinter clatters out an answer to the student's question; Turing asks: 'Foi uma pessoa ou uma máquina que respondeu?' Choices about asking a harder question or guessing who answered"
                }
            }
        ],
        "final": {
            "id": "legado_turing",
            "epoca": "Manchester, 1953",
            "scenery_guideline": _TURING_POS_GUERRA,
            "goal": "Turing, now studying the spiral patterns of sunflowers and pine cones, faces an unjust prosecution with quiet dignity. He and the student look back at the milestones they lived together. Conclude with his enduring legacy and a warm, bittersweet farewell to the student.",
            "historical_facts": "In 1952 Turing published a pioneering paper on how patterns like stripes and spirals form in nature (morphogenesis). The same year he was prosecuted for homosexuality and subjected to chemical castration; he died in 1954. The British government apologised in 2009, he received a royal pardon in 2013, the most important award in computing bears his name (the Turing Award), and his face appeared on the £50 note in 2021.",
            "emotion": "bittersweet",
            "cannot_happen": "forgetting his impact, a purely happy uncritical ending",
            "must_happen": "Turing looks at the student with a quiet smile: 'Um dia as máquinas vão conversar com as pessoas — e tudo começou com uma fita de papel.' A bittersweet vision of the digital future Turing made possible; warm, meaningful farewell"
        }
    },

    # ── HISTÓRIA DA COMPUTAÇÃO ───────────────────────────────────────────────
    # Cada marco tem seu próprio NPC; o final herda o NPC do último marco sorteado.
    "historia_computacao": {
        # Nomes/termos desta história — usados para barrar mistura com as outras (ver termos_proibidos)
        "termos_exclusivos": ["Ada", "Lovelace", "Babbage", "Máquina Analítica", "Nota G", "ENIAC", "Bartik", "ARPANET", "Kleinrock", "UCLA", "Tomlinson", "arroba", "Berners-Lee", "World Wide Web", "CERN", "Turing", "Cambridge", "King's College", "fita infinita", "fita sem fim"],
        "scenery_guideline": "Ensure each era feels distinct but shares a high-quality anime 2D aesthetic. 1840s London: foggy streets, gaslight, brass gears, ink blueprints. 1930s Cambridge: dark wood, chalkboards, paper tape. 1940s-1990s computer labs: humming machines, cables, terminals and screens of their era.",
        "marcos": [
            {
                "id": "nota_g",
                "ano": "1843",
                "titulo": "O Primeiro Algoritmo — a Nota G",
                "evento": "Em 1843 Ada Lovelace publica suas Notas sobre a Máquina Analítica de Charles Babbage. A Nota G traz um passo a passo para a máquina calcular os números de Bernoulli — o primeiro algoritmo publicado feito para uma máquina. Ada também prevê que máquinas poderiam um dia trabalhar com música e símbolos, não apenas com números.",
                "npc_principal": "Ada Lovelace",
                "npc_visual": "1woman, young Ada Lovelace, light skin, Victorian era dress, dark hair in braided buns, elegant, aristocratic, highly intelligent expression",
                "scenery_guideline": "Era: 1840s Victorian London. Key objects: brass gears and columns of the Analytical Engine model, punched cards from a Jacquard loom, ink blueprints, quill pens and handwritten manuscripts, gas lamps, velvet curtains. Atmosphere: foggy grey London light, warm candle glow.",
                "preparacao": {
                    "epoca": "Londres, 1842",
                    "goal": "The student meets Ada Lovelace as she studies the drawings of Charles Babbage's Analytical Engine — a machine of brass gears with a memory ('Store') and a processor ('Mill'), programmed with punched cards. She has been asked to translate an article about it, but she sees much more than a calculator.",
                    "historical_facts": "Ada Lovelace met Charles Babbage in 1833, at 17, when she saw his Difference Engine. Babbage then designed the Analytical Engine, with a 'Store' (memory) and a 'Mill' (processor), programmed with punched cards borrowed from the Jacquard loom. In 1842 Ada was asked to translate Luigi Menabrea's article about the machine.",
                    "emotion": "curiosity",
                    "cannot_happen": "electricity-powered computers, internet, the machine being finished",
                    "must_happen": "Ada spreads Babbage's blueprints over the table: 'Ele vê uma máquina de contas; eu vejo uma máquina que pode seguir qualquer instrução.' Choices about examining the punched cards or the brass gears"
                },
                "momento": {
                    "epoca": "Londres, 1843",
                    "goal": "The student helps Ada finish her Notes; she writes Note G, the first published algorithm for a machine, and imagines machines that could one day compose music.",
                    "historical_facts": "Ada Lovelace's Notes on the Analytical Engine, published in 1843, were three times longer than the article she translated. Note G contained a step-by-step method for computing Bernoulli numbers — considered the first published computer program. She wrote that the Engine 'might compose elaborate pieces of music'.",
                    "emotion": "wonder",
                    "cannot_happen": "modern technology, electronic computers, the Engine actually running",
                    "must_happen": "Ada hands the student her Note G manuscript: 'A máquina não apenas calcula — ela pode executar qualquer sequência de operações que pudermos imaginar.' Choices about checking the step-by-step instructions or imagining the machine making music"
                }
            },
            {
                "id": "maquina_turing",
                "ano": "1936",
                "titulo": "A Máquina de Turing",
                "evento": "Em 1936 Alan Turing publica 'On Computable Numbers' e descreve uma máquina imaginária — uma fita sem fim, uma cabeça que lê e escreve símbolos e uma tabela de regras — capaz de executar qualquer cálculo. Ele também prova que alguns problemas nenhuma máquina jamais resolverá. É o projeto teórico de todo computador moderno.",
                "npc_principal": "Alan Turing",
                "npc_visual": "1man, young Alan Turing, 20s, light skin, youthful face, athletic build, bright blue eyes, unruly messy dark hair, wearing a rumpled academic tweed jacket, white shirt without a tie, focused and intelligent expression",
                "scenery_guideline": "Era: 1930s Cambridge. Key objects: chalk-covered blackboards with logic symbols, long rolls of paper tape, dark oak desks, stacks of mathematics books, teacups, gothic stone windows. Atmosphere: grey English light, quiet library calm.",
                "preparacao": {
                    "epoca": "King's College, Cambridge, 1935",
                    "goal": "The student meets a young Alan Turing obsessed with Hilbert's question: is there a mechanical method that can decide any mathematical problem? Nobody yet knows what a 'mechanical method' even is.",
                    "historical_facts": "In 1935 Turing heard about David Hilbert's Entscheidungsproblem (the 'decision problem') in Max Newman's lectures at Cambridge. To answer it, he first had to define precisely what it means for a person — or a machine — to compute something.",
                    "emotion": "curiosity",
                    "cannot_happen": "computers already built and running, internet, World War II",
                    "must_happen": "Turing chalks the question on the board: 'O que exatamente significa calcular?' Choices about imagining a clerk following rules or a machine following rules"
                },
                "momento": {
                    "epoca": "Cambridge, 1936",
                    "goal": "Turing finishes 'On Computable Numbers', defining computability with his thought-experiment machine and proving that some problems, like the Halting Problem, can never be solved by any algorithm.",
                    "historical_facts": "In 'On Computable Numbers' (1936), Turing defined computability with his thought-experiment machine and proved that some problems are undecidable — no algorithm can ever solve them. The Halting Problem is the most famous example. This paper is the conceptual blueprint for every digital computer.",
                    "emotion": "contemplation",
                    "cannot_happen": "computers already built and running, internet",
                    "must_happen": "Turing draws a tape on the chalkboard: 'Como saber se um problema pode ser resolvido por uma máquina? Talvez alguns nunca possam.' Choices about symbols on the tape or a traditional mathematical proof"
                }
            },
            {
                "id": "eniac",
                "ano": "1946",
                "titulo": "O ENIAC e Suas Programadoras",
                "evento": "Em fevereiro de 1946 o ENIAC, um dos primeiros computadores eletrônicos, é apresentado ao público na Universidade da Pensilvânia. Ele calculou a trajetória de um projétil em 20 segundos — mais rápido do que o próprio projétil voaria. Quem o programou foram seis mulheres, entre elas Jean Jennings Bartik, que nem foram apresentadas na cerimônia.",
                "npc_principal": "Jean Jennings Bartik",
                "npc_visual": "1woman, Jean Jennings Bartik, young woman in her early 20s, light skin, shoulder-length wavy brown hair, 1940s blouse and knee-length skirt, cheerful determined expression",
                "scenery_guideline": "Era: 1940s Philadelphia, University of Pennsylvania. Key objects: the ENIAC computer (a U-shaped wall of black metal panels filling a whole room, with thousands of glowing vacuum tubes, plugboards, tangled patch cables, rows of switches and blinking neon lights), punched cards, wiring diagrams. Atmosphere: hot room, humming electricity, 1940s laboratory lights.",
                "preparacao": {
                    "epoca": "Universidade da Pensilvânia, Filadélfia, 1945",
                    "goal": "The student joins Jean Jennings and the other ENIAC programmers. There are no programming languages and no manuals: to program the giant machine they must study its wiring diagrams and plug hundreds of cables by hand.",
                    "historical_facts": "ENIAC was built during World War II to calculate artillery firing tables. Six women — Kathleen McNulty, Jean Jennings, Betty Snyder, Marlyn Wescoff, Frances Bilas and Ruth Lichterman — were chosen to program it. With no manuals, they learned the machine from its wiring diagrams and programmed it by setting switches and plugging cables.",
                    "emotion": "determination",
                    "cannot_happen": "keyboards, screens, programming languages, transistors",
                    "must_happen": "Jean holds up a tangle of cables in front of the wall of vacuum tubes: 'Não tem manual. Então nós vamos escrever o manual.' Choices about studying the wiring diagrams or testing one panel at a time"
                },
                "momento": {
                    "epoca": "Universidade da Pensilvânia, fevereiro de 1946",
                    "goal": "ENIAC's public demonstration. The program Jean and her colleagues prepared calculates a shell trajectory faster than the shell itself would fly. The audience applauds the machine — but almost no one notices the women who made it work.",
                    "historical_facts": "ENIAC was unveiled to the press on 14-15 February 1946. Running the trajectory program written by Jean Jennings and Betty Snyder, it calculated in 20 seconds a trajectory that a shell took 30 seconds to fly. The programmers were not introduced at the celebration dinner; their role was recognised only decades later.",
                    "emotion": "pride",
                    "cannot_happen": "transistors, personal computers, the programmers being publicly celebrated at the time",
                    "must_happen": "The lights of ENIAC blink as the result appears; Jean whispers to the student: 'Vinte segundos. E fomos nós que ensinamos a máquina.' Choices about telling the reporters who programmed it or checking the result once more"
                }
            },
            {
                "id": "arpanet_lo",
                "ano": "1969",
                "titulo": "A Primeira Mensagem da Internet",
                "evento": "Em 29 de outubro de 1969 a ARPANET envia a primeira mensagem entre dois computadores distantes, da UCLA para o Instituto de Pesquisa de Stanford (SRI). A palavra seria 'LOGIN', mas o sistema travou depois de 'L' e 'O'. Por acidente, 'LO' virou a primeira mensagem da rede que daria origem à internet.",
                "npc_principal": "Leonard Kleinrock",
                "npc_visual": "1man, Leonard Kleinrock, 1960s, about 35 years old, light skin, short dark hair, dark-rimmed glasses, white short-sleeve dress shirt and thin dark tie, energetic professor look",
                "scenery_guideline": "Era: 1969 UCLA computer lab. Key objects: refrigerator-sized grey computer cabinets, the IMP network box, teletype terminals printing on paper rolls, rotary telephones, reels of magnetic tape, fluorescent ceiling lights. Atmosphere: late night, humming machines, coffee cups.",
                "preparacao": {
                    "epoca": "UCLA, Los Angeles, setembro de 1969",
                    "goal": "The student joins Professor Leonard Kleinrock's lab as a strange new box arrives: the IMP, the first node of ARPANET. Kleinrock explains his idea: split messages into small packets that find their own way through the network.",
                    "historical_facts": "ARPANET was a US research network funded by the Department of Defense. It used packet switching — data split into small packets that travel independently and are reassembled at the destination. On 2 September 1969 the first IMP (Interface Message Processor) was installed in Kleinrock's lab at UCLA.",
                    "emotion": "anticipation",
                    "cannot_happen": "internet already existing, modern web browsers, smartphones",
                    "must_happen": "Kleinrock pats the refrigerator-sized IMP: 'Cada mensagem vai em pedacinhos, e cada pedacinho acha o próprio caminho.' Choices about testing the cables or calling the team at Stanford"
                },
                "momento": {
                    "epoca": "UCLA, 29 de outubro de 1969, 22h30",
                    "goal": "The student sits at the terminal as the first message is sent to SRI — and the system crashes after two letters, 'LO'.",
                    "historical_facts": "On 29 October 1969 student programmer Charley Kline, in Leonard Kleinrock's lab at UCLA, tried to type 'LOGIN' to the SRI computer, talking to the other side by telephone. The system crashed after 'L' and 'O'; about an hour later the full login worked.",
                    "emotion": "urgency",
                    "cannot_happen": "internet already existing, modern web browsers, smartphones",
                    "must_happen": "The terminal shows only 'LO' before crashing; Kleinrock grins: 'Dois caracteres. O começo de tudo.' Choices about restarting the connection or calling SRI on the telephone"
                }
            },
            {
                "id": "email_arroba",
                "ano": "1971",
                "titulo": "O Primeiro E-mail e o @",
                "evento": "Em 1971 o engenheiro Ray Tomlinson envia o primeiro e-mail entre dois computadores diferentes pela ARPANET e escolhe o símbolo @ para separar o nome da pessoa do nome do computador — o mesmo @ que usamos até hoje em todos os endereços de e-mail.",
                "npc_principal": "Ray Tomlinson",
                "npc_visual": "1man, Ray Tomlinson, about 30 years old, light skin, short dark hair, 1970s plaid shirt and corduroy trousers, friendly curious expression",
                "scenery_guideline": "Era: 1971 BBN offices, Cambridge, Massachusetts. Key objects: two large PDP-10 computer cabinets side by side, teletype terminal with a paper roll, keyboard with the @ key, magnetic tape reels, stacks of printouts. Atmosphere: 1970s office with fluorescent lights and wood paneling.",
                "preparacao": {
                    "epoca": "Empresa BBN, Cambridge (EUA), 1971",
                    "goal": "The student works with Ray Tomlinson, who already has a program to leave messages for people using the SAME computer. He wonders: what if a message could travel through ARPANET to a person on a different computer?",
                    "historical_facts": "In 1971 people could already leave messages for other users of the same computer with a program called SNDMSG. Ray Tomlinson, an engineer at the company BBN, had just written a program to send files between computers on ARPANET, and had the idea of combining the two.",
                    "emotion": "curiosity",
                    "cannot_happen": "the internet as we know it, smartphones, web browsers",
                    "must_happen": "Ray taps the side of the computer: 'E se a mensagem pudesse viajar até outra máquina?' Choices about combining the two programs or how to write the address of the receiver"
                },
                "momento": {
                    "epoca": "Empresa BBN, Cambridge (EUA), final de 1971",
                    "goal": "Ray sends the first network e-mail between two computers standing side by side, connected only through ARPANET, and picks the @ symbol for the address. The student sees the message arrive on the other machine.",
                    "historical_facts": "In late 1971 Ray Tomlinson sent the first e-mail between two different computers on ARPANET. He chose '@' to separate the user's name from the computer's name because it was a symbol that never appeared in names. He said the first message was forgettable, something like 'QWERTYUIOP'.",
                    "emotion": "delight",
                    "cannot_happen": "the internet as we know it, smartphones, web browsers",
                    "must_happen": "Ray presses the @ key and smiles: 'Nome, arroba, máquina. Simples assim.' Choices about writing the first message or walking to the other computer to see it arrive"
                }
            },
            {
                "id": "world_wide_web",
                "ano": "1991",
                "titulo": "A World Wide Web",
                "evento": "Em 6 de agosto de 1991 Tim Berners-Lee, cientista do CERN, abre ao público a World Wide Web — o sistema de páginas ligadas por links que usamos na internet. Ele criou o primeiro site, o primeiro navegador e a linguagem HTML. Em 1993 o CERN liberou a Web de graça para todo mundo.",
                "npc_principal": "Tim Berners-Lee",
                "npc_visual": "1man, Tim Berners-Lee, about 35 years old, light skin, short light brown hair, slim face, 1990s casual shirt and sweater, enthusiastic expression",
                "scenery_guideline": "Era: 1989-1991 CERN, Geneva. Key objects: black NeXT cube computer with a monitor showing the first web browser, a printed proposal document, cables, piles of physics papers, a hand-written sticker on the computer. Atmosphere: modern research office, Alps visible through the window.",
                "preparacao": {
                    "epoca": "CERN, Genebra, março de 1989",
                    "goal": "At CERN thousands of scientists struggle to share information stored in incompatible computers. The student helps Tim Berners-Lee write a proposal for a system of linked documents. His boss reads it and writes on the cover: 'Vague but exciting'.",
                    "historical_facts": "In March 1989 Tim Berners-Lee wrote 'Information Management: A Proposal' at CERN, describing a system of documents linked by hypertext over the internet. His boss Mike Sendall wrote on it 'Vague but exciting...' and let him continue. He built the first web server and browser on a NeXT computer.",
                    "emotion": "hope",
                    "cannot_happen": "web browsers already existing, smartphones, social networks",
                    "must_happen": "Tim shows the cover of his proposal with the note 'Vague but exciting': 'Vago, mas empolgante — já é um começo!' Choices about drawing the links between documents or naming the new system"
                },
                "momento": {
                    "epoca": "CERN, Genebra, 6 de agosto de 1991",
                    "goal": "Tim opens the World Wide Web to the public. The student watches the first website, info.cern.ch, become reachable by anyone on the internet.",
                    "historical_facts": "On 6 August 1991 Tim Berners-Lee announced the World Wide Web publicly and the first website, info.cern.ch, explained what the Web was. He created HTML, HTTP and URLs. In April 1993 CERN made the Web technology free for anyone to use, which allowed it to spread across the world.",
                    "emotion": "joy",
                    "cannot_happen": "smartphones, social networks, the Web being sold or patented",
                    "must_happen": "Tim clicks a blue link on the NeXT screen and another page opens: 'Agora qualquer pessoa pode ligar uma ideia a outra.' Choices about creating a new page or sending the link to a friend"
                }
            }
        ],
        "final": {
            "id": "legado_computacao",
            "epoca": "o mesmo lugar do último marco, à noite",
            "goal": "The NPC and the student look back at the milestones they lived — and at everything that came before and after: from Ada's Note G to today's connected world. Warm farewell connecting the eras of the journey.",
            "historical_facts": "Ada Lovelace's Note G (1843), Turing's machine (1936), ENIAC (1946), ARPANET (1969), e-mail (1971) and the World Wide Web (1991) are links in the same chain. Today more than 5 billion people use the internet, and every computer and smartphone is a descendant of these ideas.",
            "emotion": "gratitude",
            "cannot_happen": "forgetting the pioneers, a cold technical ending",
            "must_happen": "The NPC looks at the student with a smile: 'O que começou aqui ainda não terminou — agora é a sua vez.' Warm farewell connecting all eras of the journey"
        }
    },

    # ── KATHERINE JOHNSON ────────────────────────────────────────────────────
    "katherine_johnson": {
        # Nomes/termos desta história — usados para barrar mistura com as outras (ver termos_proibidos)
        "termos_exclusivos": ["Katherine", "Johnson", "NASA", "NACA", "Langley", "Apollo", "Glenn", "Shepard", "Armstrong", "Freedom 7", "Friendship 7", "Sputnik", "IBM 7090", "Dorothy", "Vaughan", "foguete", "astronauta", "astronautas"],
        "npc_principal": "Katherine Johnson",
        "npc_global_visual": "1woman, African American woman, dark-skinned female, very dark skin, short tightly curled black hair, cat-eye glasses with dark frames, pearl earrings, 1950s professional beige skirt suit with white collar, holding a mechanical pencil, calm confident intelligent expression",
        "scenery_guideline": "Era: 1950s-1970s NASA Langley Research Center and Mission Control, Hampton Virginia. Key locations: West Area Computing bullpen (large open office with rows of desks), Mission Control Houston (banks of flickering monitors and consoles with rows of men in white shirts and thin ties), rocket launch viewing areas. Key objects: IBM 7090 mainframe computer (enormous room-filling metal cabinet with blinking lights and reel-to-reel tape drives), mechanical Friden calculators (heavy chrome desktop adding machines), hand-ruled trajectory charts on large graph paper, manila folders stuffed with calculations, chalkboards with orbital equations and velocity vectors, rotary telephones, American flag, NASA logo placard, 1960s fluorescent office lighting, clip-on security badges. Signs visible: 'COLORED COMPUTERS' and 'WHITE COMPUTERS' (segregation era). Atmosphere: fluorescent lit 1950s government office, optimistic Space Race energy mixed with racial tension, black-and-white NASA mission photography on walls.",
        "marcos": [
            {
                "id": "sputnik_corrida",
                "ano": "1957",
                "titulo": "O Sputnik e a Corrida Espacial",
                "evento": "Em 4 de outubro de 1957 a União Soviética lança o Sputnik, o primeiro satélite artificial da história. Começa a Corrida Espacial. Em Langley, Katherine Johnson ajuda a preparar as aulas 'Notes on Space Technology' (1958), que ensinam os engenheiros americanos a pensar em voos espaciais — e no ano seguinte nasce a NASA.",
                "preparacao": {
                    "epoca": "NACA Langley, Hampton (Virgínia), 1953",
                    "goal": "Introduce Katherine as a brilliant 'Human Computer' newly arrived in the segregated West Area Computing unit. Show the daily injustice of segregation — separate bathrooms, coffee pots labelled 'Colored' — and the brilliance that gets her moved to the Flight Research Division.",
                    "historical_facts": "Katherine Johnson joined the West Area Computing unit at Langley (then part of NACA) in 1953 — a segregated group of Black women mathematicians led by Dorothy Vaughan. Laws forced them to use separate bathrooms, dining areas and even coffee pots. Within weeks her mastery of analytic geometry got her assigned to the Flight Research Division.",
                    "emotion": "determination",
                    "cannot_happen": "rockets launched, satellites in orbit, modern electronic calculators, complete racial equality",
                    "must_happen": "Katherine, surrounded by segregated 'Colored' signs, taps her pencil on a calculation sheet: 'Os números não mentem — e a matemática não conhece cor.' Choices about solving a problem the engineers got wrong or confronting an unjust rule"
                },
                "momento": {
                    "epoca": "NACA Langley, outubro de 1957",
                    "goal": "The radio announces the Soviet Sputnik and everyone at Langley runs outside to listen to its 'beep-beep'. The Space Race has begun, and the student watches Katherine realise that her equations will now have to describe flights into space.",
                    "historical_facts": "On 4 October 1957 the Soviet Union launched Sputnik 1, the first artificial satellite; amateur radios around the world picked up its beeps. The shock pushed the United States into the Space Race. Katherine Johnson contributed mathematics to 'Notes on Space Technology' (1958), lectures that taught engineers about spaceflight, and in October 1958 NACA became NASA.",
                    "emotion": "astonishment",
                    "cannot_happen": "Americans already in space, the Moon landing, modern GPS",
                    "must_happen": "A crackling radio plays Sputnik's beeps as the engineers fall silent; Katherine: 'Agora o céu virou um problema de matemática.' Choices about calculating Sputnik's orbit or joining the space lectures"
                }
            },
            {
                "id": "primeira_autora",
                "ano": "1960",
                "titulo": "A Primeira Mulher Autora na Divisão",
                "evento": "Em 1960 Katherine Johnson e o engenheiro Ted Skopinski publicam um relatório sobre como posicionar um satélite sobre um ponto exato da Terra. É a primeira vez que uma mulher da Divisão de Pesquisa de Voo da NASA recebe crédito como autora de um relatório — numa época em que o trabalho das mulheres costumava ficar sem nome.",
                "preparacao": {
                    "epoca": "NASA Langley, 1958-1959",
                    "goal": "Katherine works with the engineers of the Flight Research Division but is kept out of their briefings, and her name never appears on the reports built on her calculations. The student watches her ask a simple, brave question: is there a law against her being there?",
                    "historical_facts": "Women at Langley, and especially Black women, were not invited to the engineers' technical briefings. Katherine kept asking to attend; when told women did not go, she asked whether there was a law against it. There wasn't, and she began attending. Until then, the women's calculations usually appeared in reports without their names.",
                    "emotion": "courage",
                    "cannot_happen": "rockets carrying astronauts, the Moon landing, complete equality",
                    "must_happen": "Katherine stands at the door of the briefing room: 'Existe alguma lei que me proíba de entrar?' Choices about entering the meeting or presenting her calculations to the engineers"
                },
                "momento": {
                    "epoca": "NASA Langley, 1960",
                    "goal": "Katherine's report with Ted Skopinski is published with her name on the cover. The student sees her hold the printed document — the first in her division credited to a woman.",
                    "historical_facts": "In 1960 Katherine Johnson and engineer Ted Skopinski co-authored 'Determination of Azimuth Angle at Burnout for Placing a Satellite Over a Selected Earth Position'. It was the first time a woman in the Flight Research Division received credit as an author of a research report. She went on to author or co-author 26 research reports.",
                    "emotion": "pride",
                    "cannot_happen": "astronauts already in orbit, modern computers doing the work, complete equality",
                    "must_happen": "Katherine runs her finger over her printed name on the report cover: 'Agora o meu nome está aqui — e vai ficar.' Choices about starting the next calculation or showing the report to the other women of West Computing"
                }
            },
            {
                "id": "freedom7",
                "ano": "1961",
                "titulo": "O Primeiro Americano no Espaço",
                "evento": "Em 5 de maio de 1961 a cápsula Freedom 7 leva Alan Shepard ao espaço — o primeiro americano a ir além da atmosfera. Katherine Johnson calculou à mão a trajetória do voo e a janela de lançamento, para que a cápsula caísse no oceano exatamente onde os navios de resgate estariam esperando.",
                "preparacao": {
                    "epoca": "NASA Langley, início de 1961",
                    "goal": "The Soviets are ahead in the Space Race and the first American flight is coming. The student helps Katherine work out the trajectory and launch window for Alan Shepard's capsule: if the numbers are wrong, the ships will not be there to rescue him.",
                    "historical_facts": "For Project Mercury, Katherine Johnson did the trajectory analysis for Alan Shepard's suborbital flight, working with pencil, slide rule and mechanical calculators. She had to calculate where the capsule would land so the recovery ships could wait at the right spot in the Atlantic. In April 1961 the Soviet Yuri Gagarin became the first human in space.",
                    "emotion": "pressure",
                    "cannot_happen": "modern GPS, the flight already done, the Moon landing",
                    "must_happen": "Katherine pins a map of the Atlantic to the wall: 'Me diga onde ele começa, e eu digo onde ele vai cair.' Choices about re-checking the launch window or plotting the landing spot on the map"
                },
                "momento": {
                    "epoca": "NASA Langley, 5 de maio de 1961",
                    "goal": "Launch day. The student follows the radio with Katherine as Freedom 7 carries Alan Shepard into space and splashes down exactly where she predicted.",
                    "historical_facts": "On 5 May 1961 Freedom 7 carried Alan Shepard on a 15-minute suborbital flight, making him the first American in space. The capsule splashed down in the Atlantic close to the recovery ship, as Katherine's calculations predicted.",
                    "emotion": "pride",
                    "cannot_happen": "modern GPS, Shepard orbiting the Earth, the Moon landing",
                    "must_happen": "Katherine follows the radio countdown with her trajectory sheet in hand: 'Se a conta estiver certa, ele cai exatamente aqui.' Choices about following the splashdown on the radio or celebrating with the team"
                }
            },
            {
                "id": "friendship7",
                "ano": "1962",
                "titulo": "John Glenn em Órbita",
                "evento": "Em 20 de fevereiro de 1962 John Glenn se torna o primeiro americano a dar a volta na Terra em órbita, a bordo da Friendship 7. Antes de partir, ele não confiou só no novo computador IBM e pediu que Katherine Johnson conferisse os cálculos à mão: 'Se ela disser que os números estão certos, eu vou.'",
                "preparacao": {
                    "epoca": "NASA Langley, fevereiro de 1962",
                    "goal": "John Glenn is about to orbit the Earth, but he does not trust the new IBM 7090 computer. He refuses to fly unless Katherine Johnson personally verifies the machine's numbers by hand. Show the pressure, the clock, the doubt between human and machine. The flight has NOT happened yet.",
                    "historical_facts": "Before his Friendship 7 orbital flight, astronaut John Glenn distrusted the new IBM 7090 computers. He asked engineers to 'get the girl' to check the numbers: 'If she says they're good, then I'm ready to go.' Katherine spent about a day and a half verifying the orbital equations by hand.",
                    "emotion": "pressure",
                    "cannot_happen": "the computer being trusted blindly, modern GPS, the flight already done",
                    "must_happen": "A NASA engineer bursts in: 'Glenn quer você, Katherine — se você disser que os números estão certos, ele vai.' Choices about verifying the IBM output from scratch or comparing it line by line"
                },
                "momento": {
                    "epoca": "NASA, 20 de fevereiro de 1962",
                    "goal": "Friendship 7 launches. The student and Katherine follow John Glenn as he circles the Earth three times and comes home safely — the numbers she checked by hand were right.",
                    "historical_facts": "On 20 February 1962 John Glenn orbited the Earth three times in Friendship 7, a flight of almost five hours, becoming the first American in orbit. He splashed down safely in the Atlantic. His trust in Katherine's verification became one of the most famous stories of the Space Race.",
                    "emotion": "relief",
                    "cannot_happen": "the mission failing, modern GPS, the Moon landing",
                    "must_happen": "The radio crackles with Glenn's voice from orbit; Katherine follows each orbit on her chart: 'Primeira volta... segunda... terceira. Os números estavam certos.' Choices about tracking the re-entry or calling Dorothy Vaughan with the news"
                }
            },
            {
                "id": "apollo11",
                "ano": "1969",
                "titulo": "A Chegada do Homem à Lua",
                "evento": "Em 20 de julho de 1969 o módulo lunar Eagle da Apollo 11 pousa na Lua, e Neil Armstrong dá o primeiro passo humano em outro mundo. Katherine Johnson ajudou a calcular a trajetória até a Lua e o encontro do módulo lunar com a nave de comando para a volta — sem esse cálculo, os astronautas não voltariam para casa.",
                "preparacao": {
                    "epoca": "NASA Langley, 1968",
                    "goal": "The Moon is the goal. The student helps Katherine with the hardest problem: after landing, the small lunar module must take off and meet the command module circling the Moon — two ships finding each other in space. Doubt and long nights of calculation.",
                    "historical_facts": "For the Apollo programme, Katherine Johnson worked on the trajectory to the Moon and on the rendezvous paths that let the lunar module meet the orbiting command module for the trip home. She also prepared backup procedures and star charts so astronauts could navigate if electronics failed.",
                    "emotion": "concentration",
                    "cannot_happen": "the Moon landing already done, modern GPS, the mission failing",
                    "must_happen": "Katherine draws two circles around a sketch of the Moon: 'Duas naves, uma pequena e uma grande, precisam se encontrar no escuro.' Choices about calculating the take-off moment or preparing the backup star charts"
                },
                "momento": {
                    "epoca": "NASA, 20 de julho de 1969",
                    "goal": "The student and Katherine follow the Apollo 11 landing; the numbers she helped calculate guide the Eagle to the Moon. Show the breath-holding silence until 'The Eagle has landed'.",
                    "historical_facts": "On 20 July 1969 Apollo 11's lunar module Eagle landed in the Sea of Tranquility and Neil Armstrong became the first person to walk on the Moon. Katherine Johnson had worked on the calculations for the trajectory and for the rendezvous that brought the astronauts home.",
                    "emotion": "awe",
                    "cannot_happen": "the mission failing, modern GPS, the Apollo 13 accident",
                    "must_happen": "The room holds its breath until the radio says 'The Eagle has landed'; Katherine looks at her charts: 'Agora eles precisam voltar — e a volta também está nestes números.' Choices about checking the return rendezvous or watching Armstrong's first step"
                }
            },
            {
                "id": "apollo13",
                "ano": "1970",
                "titulo": "O Resgate da Apollo 13",
                "evento": "Em abril de 1970 um tanque de oxigênio explode na Apollo 13 a caminho da Lua. Com a nave danificada, a NASA usa os procedimentos de reserva e as cartas de estrelas que Katherine Johnson tinha preparado para calcular uma rota de volta. Em 17 de abril os três astronautas pousam no oceano, sãos e salvos.",
                "preparacao": {
                    "epoca": "NASA, 13 de abril de 1970",
                    "goal": "'Houston, we've had a problem.' An oxygen tank has exploded on Apollo 13, far from Earth. The student is beside Katherine as the alarm spreads: the computers on the ship can no longer be trusted, and three lives depend on finding a way home.",
                    "historical_facts": "On 13 April 1970, about 56 hours into the flight, an oxygen tank exploded on Apollo 13, crippling the command module. The crew moved into the lunar module, using it as a lifeboat, and engineers on the ground had to work out a new trajectory home with limited power and navigation.",
                    "emotion": "fear",
                    "cannot_happen": "astronauts dying, modern GPS, the rescue already finished",
                    "must_happen": "The radio crackles 'Houston, we've had a problem'; Katherine opens a folder of old backup charts: 'Eu preparei isso anos atrás, para um dia como hoje.' Choices about using the star charts or calculating a slingshot around the Moon"
                },
                "momento": {
                    "epoca": "NASA, 17 de abril de 1970",
                    "goal": "Using Katherine's backup procedures and star charts, the crew navigates around the Moon and back to Earth. The student watches the silent minutes of re-entry until the three parachutes appear.",
                    "historical_facts": "Apollo 13 swung around the Moon and returned to Earth using its gravity. Katherine Johnson's earlier work on backup procedures and star charts helped the crew navigate when normal systems failed. On 17 April 1970 the three astronauts splashed down safely in the Pacific.",
                    "emotion": "gratitude",
                    "cannot_happen": "astronauts dying, modern GPS",
                    "must_happen": "After minutes of radio silence the parachutes appear on the screen; Katherine closes her eyes: 'Eles estão em casa.' Choices about thanking the team or keeping the star chart as a memory"
                }
            }
        ],
        "final": {
            "id": "legado_katherine",
            "epoca": "NASA Langley, 1986",
            "npc_visual": "1woman, elderly African American woman, dark-skinned female, very dark skin, short curly grey hair, glasses, elegant 1980s blouse and cardigan, warm wise smile",
            "goal": "Katherine's last day at NASA after 33 years. She and the student look back at the milestones they lived together, and she speaks about the future she will not see but already imagines. Warm, earned farewell celebrating her full legacy.",
            "historical_facts": "Katherine Johnson retired from NASA in 1986 after 33 years. In 2015 President Obama awarded her the Presidential Medal of Freedom; in 2016 the film Hidden Figures told her story; in 2017 NASA opened the Katherine G. Johnson Computational Research Facility. She passed away on 24 February 2020, aged 101.",
            "emotion": "gratitude",
            "cannot_happen": "forgetting her contributions, remaining historically hidden",
            "must_happen": "Katherine hands the student her old mechanical pencil: 'Conte com a matemática. Ela nunca mente.' Warm, earned farewell celebrating her full legacy"
        }
    }
}


def montar_steps(modelo, marcos):
    """
    Monta as 5 cenas da sessão a partir dos marcos sorteados (em ordem cronológica):
    preparação A → ★ marco A → preparação B → ★ marco B → final.
    """
    steps = []
    for n, marco in enumerate(marcos):
        base = {"npc_principal": marco.get("npc_principal", modelo.get("npc_principal", ""))}
        for campo in ("npc_visual", "scenery_guideline"):
            if campo in marco:
                base[campo] = marco[campo]
        # A preparação do 2º marco vem depois de um salto no tempo
        steps.append({"id": f"{marco['id']}_preparacao", **base, **marco["preparacao"], "salto_temporal": n > 0})
        steps.append({"id": marco["id"], **base, **marco["momento"],
                      "marco_historico": {k: marco[k] for k in ("ano", "titulo", "evento")}})

    final = dict(modelo["final"])
    # Final sem NPC próprio herda o do último marco (ex.: história da computação)
    for campo in ("npc_principal", "npc_visual"):
        if campo not in final and campo in steps[-1]:
            final[campo] = steps[-1][campo]
    final["salto_temporal"] = True
    steps.append(final)
    return steps


def termos_proibidos(focus_skill):
    """
    Termos que pertencem SÓ a outras histórias (ex.: "Turing" numa história da Katherine).
    Se aparecerem no texto ou nas opções, a cena misturou histórias.
    """
    proprios = {t.lower() for t in BLUEPRINTS.get(focus_skill, {}).get("termos_exclusivos", [])}
    outros = {t for skill, bp in BLUEPRINTS.items() if skill != focus_skill for t in bp.get("termos_exclusivos", [])}
    return sorted(t for t in outros if t.lower() not in proprios)


def sortear_blueprint(focus_skill):
    """Sorteia os marcos da sessão e devolve o blueprint com as 5 cenas montadas."""
    modelo = BLUEPRINTS.get(focus_skill) or BLUEPRINTS[next(iter(BLUEPRINTS))]
    indices = sorted(random.sample(range(len(modelo["marcos"])), MARCOS_POR_HISTORIA))
    marcos = [modelo["marcos"][i] for i in indices]
    return {
        "npc_global_visual": modelo.get("npc_global_visual", ""),
        "scenery_guideline": modelo.get("scenery_guideline", ""),
        "marcos_sorteados": [m["id"] for m in marcos],
        "steps": montar_steps(modelo, marcos),
    }


class StateManager:
    def __init__(self):
        self.sessions = {}

    def create_session(self, student_name, focus_skill, theme):
        session_id = str(datetime.now().timestamp()).replace(".", "")
        
        # Sorteia os marcos históricos desta sessão e monta as 5 cenas
        # (skill desconhecida cai na primeira história disponível)
        blueprint = sortear_blueprint(focus_skill)
        
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
            "termos_proibidos": termos_proibidos(state["student"].get("focus_skill", "")),
            "student_genero": state["student"].get("genero", "Masculino"),
            "theme": state["student"]["theme"],
            "current_step": step["id"],
            "skill": state["student"].get("focus_skill", ""),
            "npc_principal": step.get("npc_principal", ""),
            "npc_visual": step.get("npc_visual", state["blueprint"].get("npc_global_visual", "")),
            "scenery_guideline": step.get("scenery_guideline", state["blueprint"].get("scenery_guideline", "")),
            "epoca": step.get("epoca", ""),
            # True quando a cena começa depois de um salto no tempo (preparação do 2º marco e final)
            "salto_temporal": step.get("salto_temporal", False),
            "goal": step["goal"],
            "historical_facts": step.get("historical_facts", ""),
            "emotion": step["emotion"],
            "cannot_happen": step["cannot_happen"],
            "must_happen": step["must_happen"],
            "is_final": idx == total - 1,
            "ato": ato,
            "step_index": idx,
            "total_steps": total,
            # Marco histórico deste capítulo (None se não for um marco)
            "marco_historico": step.get("marco_historico"),
            # Todos os marcos da jornada, para o LLM não antecipar um marco fora do seu capítulo
            "marcos_jornada": [
                {"capitulo": i + 1, **s["marco_historico"]}
                for i, s in enumerate(state["blueprint"]["steps"])
                if s.get("marco_historico")
            ]
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
