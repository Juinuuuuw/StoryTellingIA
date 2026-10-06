# nao_speaker_v2.py
import json
import time
import urllib.request
import os
import sys
import subprocess
import random
import shlex
import threading
from naoguese import para_naoguese  # transliteração fonética PT-BR → NAOguês

try:
    import paramiko
    PARAMIKO_DISPONIVEL = True
except ImportError:
    PARAMIKO_DISPONIVEL = False

try:
    import qi  # type: ignore
    QI_DISPONIVEL = True
except ImportError:
    QI_DISPONIVEL = False

SERVER_URL       = "http://127.0.0.1:5000/visualizador/cena_atual"
SERVER_QUADRO    = "http://127.0.0.1:5000/visualizador/quadro_atual"
NAO_IP     = "172.20.10.5"
NAO_PORT   = 9559

# Pausa depois de terminar a fala de um quadro, antes de liberar a troca de imagem
PAUSA_APOS_FALA_QUADRO = 1.2
# A configuração de atenção é reaplicada de tempos em tempos: a Vida Autônoma do NAO
# pode restaurar o padrão (que reage a sons) quando muda de estado
REAPLICAR_ATENCAO_A_CADA = 60

# ============================================================
# ATENÇÃO: olhar para a pessoa na frente, sem virar a cabeça por barulho
# ============================================================
# O padrão do NAO (ALBasicAwareness) vira a cabeça na direção de qualquer som ou
# movimento — é o giro rápido "do nada". Aqui ele só segue PESSOAS e, ao engajar
# com alguém (FullyEngaged), ignora os outros estímulos até perder essa pessoa.
# (serviço, método, argumentos) — cada comando é independente: se um não existir
# nesta versão do NAOqi, os outros continuam valendo.
CONFIG_ATENCAO = [
    ("ALAutonomousLife",  "setAutonomousAbilityEnabled", ["BackgroundMovement", False]),  # mexidas aleatórias
    ("ALAutonomousLife",  "setAutonomousAbilityEnabled", ["ListeningMovement", False]),
    ("ALAutonomousMoves", "setExpressiveListeningEnabled", [False]),
    ("ALAutonomousMoves", "setBackgroundStrategy", ["none"]),
    ("ALBasicAwareness",  "setStimulusDetectionEnabled", ["Sound", False]),
    ("ALBasicAwareness",  "setStimulusDetectionEnabled", ["Movement", False]),
    ("ALBasicAwareness",  "setStimulusDetectionEnabled", ["NavigationMotion", False]),
    ("ALBasicAwareness",  "setStimulusDetectionEnabled", ["Touch", False]),
    ("ALBasicAwareness",  "setStimulusDetectionEnabled", ["TabletTouch", False]),
    ("ALBasicAwareness",  "setStimulusDetectionEnabled", ["People", True]),
    ("ALBasicAwareness",  "setEngagementMode", ["FullyEngaged"]),
    ("ALBasicAwareness",  "setTrackingMode", ["Head"]),      # só a cabeça acompanha, o corpo fica parado
]

# ============================================================
# ANIMAÇÕES DISPONÍVEIS NO NAO (behavior names nativos)
# Caminho: animations/Stand/Gestures/
# ============================================================
ANIM_BASE = "animations/Stand/Gestures/"

GESTOS = {
    # Saudação
    "bemvindo":   ANIM_BASE + "Hey_1",
    "tchau":      ANIM_BASE + "Salute_1",

    # Positivo
    "animado":    ANIM_BASE + "Enthusiastic_4",
    "concordar":  ANIM_BASE + "Yes_1",
    "otimo":      ANIM_BASE + "Enthusiastic_1",

    # Negativo
    "discordar":  ANIM_BASE + "No_1",
    "triste":     ANIM_BASE + "Desperate_1",

    # Pensamento
    "pensar":     ANIM_BASE + "Think_1",
    "curioso":    ANIM_BASE + "Thinking_1",
    "duvida":     ANIM_BASE + "Confused_1",

    # Explicação
    "explicar":   ANIM_BASE + "Explain_1",
    "apontar":    ANIM_BASE + "ShowSky_1",
    "contar":     ANIM_BASE + "CountOne_1",

    # Outros
    "surpresa":   ANIM_BASE + "Surprise_1",
    "neutro":     ANIM_BASE + "Neutral_1",
}

# ============================================================
# MAPEAMENTO PALAVRA → GESTO
# ============================================================
POSES = [
    (["bem-vindo", "olá", "oi", "chegamos", "início",
      "começa", "vamos começar", "iniciar"],                      "bemvindo"),

    (["incrível", "uau", "wow", "surpreendente", "inesperado",
      "fantástico", "espantoso", "extraordinário"],               "surpresa"),

    (["parabéns", "conseguiu", "excelente", "ótimo", "perfeito",
      "vitória", "sucesso", "resolveu", "funcionou", "conquista"], "animado"),

    (["triste", "falhou", "erro", "problema", "frustrado",
      "fracasso", "infelizmente", "pena"],                        "triste"),

    (["pensa", "imagine", "questão", "como", "decidir",
      "analisar", "calcular", "resolver", "será que",
      "o que acha", "reflita", "hmm"],                            "pensar"),

    (["explica", "veja", "observe", "note", "perceba",
      "então", "portanto", "assim", "ou seja", "significa",
      "representa", "demonstra", "mostra"],                       "explicar"),

    (["sim", "correto", "exato", "certamente", "claro",
      "concordo", "está certo", "isso mesmo"],                    "concordar"),

    (["não", "nunca", "jamais", "errado", "incorreto",
      "discordo", "negativo"],                                     "discordar"),

    (["curioso", "interessante", "que estranho", "por que",
      "fascinante", "intrigante", "misterioso"],                  "curioso"),

    (["aqui está", "olha", "apresento", "este é",
      "conheça", "atenção", "aqui temos"],                        "apontar"),

    (["primeiro", "segundo", "terceiro", "primeiramente",
      "além disso", "importante", "principais"],                  "contar"),
]

# NOVO: Frases de enrolação adicionais
FRASES_ENROLACAO = [
    "Hmm, deixe-me ver...",
    "Estou processando as ideias...",
    "Interessante...",
    "Só mais um momento...",
    "Estou pensando no que vai acontecer...",
    "Quase lá...",
    "Pensando..."
]

def escolher_gesto(texto):
    texto_lower = texto.lower()
    for palavras, gesto in POSES:
        for palavra in palavras:
            if palavra in texto_lower:
                return gesto
    return "neutro"

def limpar_texto(texto):
    if not texto:
        return ""
    import re
    t = texto.replace('"', '').replace('«', '').replace('»', '')
    t = re.sub(r'[—–]', ',', t)
    t = t.replace('...', '.')
    t = re.sub(r'[*_~`#]', '', t)
    t = re.sub(r'\s{2,}', ' ', t)
    return t.strip()

# ============================================================
# CONEXÃO E FALLBACK
# ============================================================
def falar_fallback(texto_animado, texto_puro):
    if not PARAMIKO_DISPONIVEL:
        print("Erro: A biblioteca 'paramiko' não está instalada e 'qi' não foi encontrado.")
        return
        
    # Tempo máximo esperando a fala terminar: se a rede cair no meio, não trava para sempre
    # (o NAO fala ~13 caracteres por segundo; a folga cobre gestos e conexão)
    limite = 20 + len(texto_puro) * 0.12
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(NAO_IP, username="nao", password="nao", timeout=5)

        # Define linguagem antes de falar
        ssh.exec_command('qicli call ALTextToSpeech.setLanguage "Brazilian"')

        # Executa ALAnimatedSpeech (espera terminar: é isso que marca o fim da fala do quadro)
        cmd = f'qicli call ALAnimatedSpeech.say "{texto_animado}"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=limite)
        erro = stderr.read().decode().strip()

        if erro or stdout.channel.recv_exit_status() != 0:
            print("SSH ALAnimatedSpeech falhou:", erro)
            print("Tentando TTS simples via SSH...")
            cmd_puro = f'qicli call ALTextToSpeech.say "{texto_puro}"'
            _, out_puro, _ = ssh.exec_command(cmd_puro, timeout=limite)
            out_puro.channel.recv_exit_status()   # espera a fala acabar antes de avisar o servidor

        ssh.close()
    except Exception as e:
        print("Erro ao tentar enviar comando via SSH para o NAO:", e)


def _executar_ssh(comando, timeout=20):
    """Roda um comando no NAO por SSH e devolve a saída (vazia se falhar)."""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(NAO_IP, username="nao", password="nao", timeout=5)
        _, stdout, _ = ssh.exec_command(comando, timeout=timeout)
        saida = stdout.read().decode(errors="replace")
        ssh.close()
        return saida
    except Exception as e:
        print("Erro de SSH com o NAO:", e)
        return ""


def configurar_atencao(silencioso=False):
    """Aplica CONFIG_ATENCAO no robô (pelo qi ou por SSH) e liga o rastreamento de pessoas."""
    falhas = []
    if QI_DISPONIVEL:
        for servico, metodo, args in CONFIG_ATENCAO:
            try:
                getattr(session.service(servico), metodo)(*args)
            except Exception:
                falhas.append(f"{servico}.{metodo}{args}")
        try:
            aw = session.service("ALBasicAwareness")
            try:
                aw.setEnabled(True)            # NAOqi 2.5+
            except Exception:
                aw.startAwareness()            # NAOqi 2.1
        except Exception:
            falhas.append("ALBasicAwareness ligar")
    elif PARAMIKO_DISPONIVEL:
        # Um único SSH com todos os comandos; --json garante o tipo certo (bool/str) de cada argumento
        linhas = []
        for servico, metodo, args in CONFIG_ATENCAO:
            argv = " ".join(shlex.quote(json.dumps(a)) for a in args)
            nome = f"{servico}.{metodo}{args}"
            linhas.append(f"qicli call --json {servico}.{metodo} {argv} >/dev/null 2>&1 || echo FALHOU:{shlex.quote(nome)}")
        linhas.append("(qicli call --json ALBasicAwareness.setEnabled true >/dev/null 2>&1"
                      " || qicli call ALBasicAwareness.startAwareness >/dev/null 2>&1) || echo FALHOU:ligar-ALBasicAwareness")
        saida = _executar_ssh("; ".join(linhas))
        falhas = [l[len("FALHOU:"):] for l in saida.splitlines() if l.startswith("FALHOU:")]
    else:
        return
    if not silencioso:
        print("Atenção configurada: o NAO segue pessoas e ignora sons/movimentos.")
        for f in falhas:
            print("  (aviso) não disponível nesta versão do NAOqi: " + f)


def _manter_atencao():
    """Reaplica a configuração periodicamente, em segundo plano (não atrasa as falas)."""
    while True:
        time.sleep(REAPLICAR_ATENCAO_A_CADA)
        configurar_atencao(silencioso=True)

if QI_DISPONIVEL:
    print("Conectando ao NAO nativamente (qi)...")
    try:
        app = qi.Application(["nao_speaker", "--qi-url", "tcp://{}:{}".format(NAO_IP, NAO_PORT)])
        app.start()
        session = app.session
        tts     = session.service("ALTextToSpeech")
        anim    = session.service("ALAnimatedSpeech")
        motion  = session.service("ALMotion")
        tts.setLanguage("Brazilian")
        config = {"bodyLanguageMode": "contextual"}
        
        # Garante que os motores da cabeça estão ligados para ela acompanhar a pessoa
        try:
            motion.setStiffnesses("Head", 1.0)
        except Exception as e:
            print("Aviso: Nao foi possivel ativar stiffness da cabeca:", e)

        print("Conectado ao NAO!")
    except Exception as e:
        print("Erro ao conectar ao NAO: " + str(e))
        raise SystemExit
else:
    print("Módulo 'qi' não encontrado no Python 3. Usando modo de envio direto via SSH (Paramiko)...")
    if not PARAMIKO_DISPONIVEL:
        print("AVISO: A biblioteca 'paramiko' não foi encontrada! Execute: pip install paramiko")
    else:
        print("Paramiko pronto para conectar ao NAO via SSH!")


# A cabeça é guiada pela atenção do NAO (segue a pessoa da frente). O antigo movimento
# ocioso aleatório foi removido: ele brigava com o rastreamento e girava a cabeça sozinho.
configurar_atencao()
threading.Thread(target=_manter_atencao, daemon=True).start()

# ============================================================
# LOOP PRINCIPAL — sincronizado por quadro
# ============================================================
ultimo_texto   = None
ultimo_quadro  = None  # (cena_id, quadro_idx) do último quadro já falado
tempo_ultima_fala = time.time()

print("Monitorando servidor... (CTRL+C para parar)")

def _sinalizar_inicio_fala():
    """Avisa o servidor que o NAO começou a falar (bloqueia avanço de quadro)."""
    try:
        urllib.request.urlopen(
            urllib.request.Request(SERVER_URL.replace("/visualizador/cena_atual", "/nao_iniciou_fala"),
                                   data=b"{}", method="POST",
                                   headers={"Content-Type": "application/json"}),
            timeout=2
        )
    except Exception:
        pass

def _sinalizar_fim_fala():
    """Avisa o servidor que o NAO terminou de falar (libera avanço de quadro)."""
    try:
        urllib.request.urlopen(
            urllib.request.Request(SERVER_URL.replace("/visualizador/cena_atual", "/nao_terminou_fala"),
                                   data=b"{}", method="POST",
                                   headers={"Content-Type": "application/json"}),
            timeout=2
        )
    except Exception:
        pass

def _avisar_fim_do_quadro(cena_id, quadro_idx):
    """
    Avisa o servidor que terminou de falar o quadro — é o gatilho de avanço da cena.
    A rede é instável: reenvia em segundo plano até o servidor confirmar. O aviso é
    absoluto ("quadro N da cena X"), então chegar repetido ou atrasado não pula quadro.
    """
    corpo = json.dumps({"cena_id": cena_id, "quadro_idx": quadro_idx}).encode()
    url = SERVER_URL.replace("/visualizador/cena_atual", "/nao_terminou_fala")

    def enviar():
        for _ in range(120):   # até ~2 min tentando
            try:
                urllib.request.urlopen(
                    urllib.request.Request(url, data=corpo, method="POST",
                                           headers={"Content-Type": "application/json"}),
                    timeout=3
                )
                return
            except Exception:
                time.sleep(1)
        print(f"Aviso: não consegui avisar o fim do quadro {quadro_idx + 1} (cena {cena_id}).")

    threading.Thread(target=enviar, daemon=True).start()


def falar(texto, quadro=None):
    global tempo_ultima_fala
    """
    Dispara a fala no NAO com gesto contextual.
    quadro=(cena_id, quadro_idx) quando a fala é de um quadro: ao terminar, avisa o
    servidor para a cena avançar.
    """
    if not texto:
        return
    texto = limpar_texto(texto)
    gesto = escolher_gesto(texto)          # usa texto original PT-BR para escolher gesto

    texto_nao = para_naoguese(texto)       # converte para NAOguês antes de falar
    print("NAO vai falar: " + texto_nao)
    print("  (original): " + texto)

    anim_path = GESTOS[gesto]
    print("Gesto: " + gesto + " (" + anim_path + ")")
    texto_animado = "^start({}) {}".format(anim_path, texto_nao)

    _sinalizar_inicio_fala()   # bloqueia avanço de quadro no frontend
    try:
        if QI_DISPONIVEL:
            anim.say(texto_animado, config)   # BLOQUEANTE — só retorna quando termina
        else:
            falar_fallback(texto_animado, texto_nao)
    except Exception as e1:
        print("ALAnimatedSpeech falhou (" + str(e1) + "), usando TTS simples...")
        try:
            if QI_DISPONIVEL:
                tts.say(texto_nao)            # BLOQUEANTE
        except Exception as e2:
            print("TTS também falhou: " + str(e2))
    finally:
        # Sempre executa, mesmo em erro
        if quadro is not None:
            time.sleep(PAUSA_APOS_FALA_QUADRO)   # respiro antes de trocar a imagem
            _avisar_fim_do_quadro(*quadro)
        else:
            _sinalizar_fim_fala()
        tempo_ultima_fala = time.time()


while True:
    agora = time.time()
    try:
        # ── Prioridade 1: estado "pensando" (enrolação enquanto IA gera) ──
        raw_cena = urllib.request.urlopen(SERVER_URL, timeout=5).read()
        cena_data = json.loads(raw_cena)

        if cena_data.get("status") == "pensando":
            texto_enrolacao = cena_data.get("fala_robo", "") or cena_data.get("fala_enrolacao", "")
            
            # Se for um novo texto de enrolação recebido do servidor, fala ele
            if texto_enrolacao and texto_enrolacao != ultimo_texto:
                ultimo_texto = texto_enrolacao
                falar(texto_enrolacao)
            else:
                # Se ainda estiver "pensando" e já se passaram 8 a 15 segundos desde a última fala, fala algo a mais
                if agora - tempo_ultima_fala > random.uniform(8, 15):
                    frase_extra = random.choice(FRASES_ENROLACAO)
                    print(f"Adicionando enrolação extra: {frase_extra}")
                    falar(frase_extra)
                    
        elif cena_data.get("status") == "comando_avulso":
            texto_comando = cena_data.get("fala_robo", "")
            if texto_comando and texto_comando != ultimo_texto:
                ultimo_texto = texto_comando
                falar(texto_comando)

        elif cena_data.get("status") == "modal":
            pergunta = cena_data.get("dados", {}).get("pergunta", "")
            if pergunta and pergunta != ultimo_texto:
                ultimo_texto = pergunta
                falar(pergunta)

        elif cena_data.get("status") == "ativo":
            # ── Prioridade 2: quadro específico sendo exibido agora ──
            raw_q = urllib.request.urlopen(SERVER_QUADRO, timeout=5).read()
            q_data = json.loads(raw_q)

            texto_quadro = q_data.get("texto", "")
            quadro_idx   = q_data.get("quadro_idx", 0)
            chave        = (q_data.get("cena_id"), quadro_idx)

            # Fala uma vez por quadro de cada cena (o cena_id evita confundir quadros de cenas diferentes)
            if texto_quadro and quadro_idx >= 0 and chave != ultimo_quadro:
                ultimo_quadro = chave
                ultimo_texto  = texto_quadro
                falar(texto_quadro, quadro=chave)

    except KeyboardInterrupt:
        print("Encerrando.")
        break
    except Exception as e:
        print("Erro: " + str(e))
        
    time.sleep(1)  # poll a cada 1s — rápido o suficiente para pegar a troca de quadro
