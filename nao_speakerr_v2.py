# nao_speaker_v2.py
import json
import time
import urllib.request
import os
import sys
import subprocess
import random
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
        
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(NAO_IP, username="nao", password="nao", timeout=5)
        
        # Define linguagem antes de falar
        ssh.exec_command('qicli call ALTextToSpeech.setLanguage "Brazilian"')
        
        # Executa ALAnimatedSpeech
        cmd = f'qicli call ALAnimatedSpeech.say "{texto_animado}"'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        erro = stderr.read().decode().strip()
        
        if erro or stdout.channel.recv_exit_status() != 0:
            print("SSH ALAnimatedSpeech falhou:", erro)
            print("Tentando TTS simples via SSH...")
            cmd_puro = f'qicli call ALTextToSpeech.say "{texto_puro}"'
            ssh.exec_command(cmd_puro)
        
        ssh.close()
    except Exception as e:
        print("Erro ao tentar enviar comando via SSH para o NAO:", e)

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
        
        # Garante que os motores da cabeça estão ligados para podermos movê-la no modo idle
        try:
            motion.setStiffnesses("Head", 1.0)
            
            # Desativa o "tracking" automático do NAO (que faz ele olhar loucamente pros lados)
            try:
                awareness = session.service("ALBasicAwareness")
                if awareness.isAwarenessRunning():
                    awareness.stopAwareness()
            except Exception:
                pass
                
            try:
                autoMoves = session.service("ALAutonomousMoves")
                autoMoves.setExpressiveListeningEnabled(False)
                autoMoves.setBackgroundStrategy("none")
            except Exception:
                pass
                
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


# NOVO: Função para movimentar a cabeça lentamente (idle look)
def mover_cabeca_idle():
    yaw = random.uniform(-0.15, 0.15)
    pitch = random.uniform(-0.10, 0.10)
    velocidade = random.uniform(0.02, 0.05)
    
    if QI_DISPONIVEL:
        try:
            motion.setAngles(["HeadYaw", "HeadPitch"], [yaw, pitch], velocidade)
        except Exception:
            pass
    elif PARAMIKO_DISPONIVEL:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(NAO_IP, username="nao", password="nao", timeout=2)
            cmd1 = f'qicli call ALMotion.setAngles "HeadYaw" {yaw} {velocidade}'
            cmd2 = f'qicli call ALMotion.setAngles "HeadPitch" {pitch} {velocidade}'
            ssh.exec_command(f"{cmd1} ; {cmd2}")
            ssh.close()
        except:
            pass

# ============================================================
# LOOP PRINCIPAL — sincronizado por quadro
# ============================================================
ultimo_texto   = None
ultimo_quadro  = -1   # rastreia o índice do quadro já falado
tempo_ultima_fala = time.time()
tempo_ultimo_movimento = time.time()

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

def falar(texto):
    global tempo_ultima_fala
    """Dispara a fala no NAO com gesto contextual."""
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
        _sinalizar_fim_fala()  # libera avanço de quadro — sempre executa, mesmo em erro
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
                ultimo_quadro = -1   # reseta para falar novamente na próxima cena
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
                ultimo_quadro = -1
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

            # Fala apenas quando o quadro muda E há texto novo
            if texto_quadro and quadro_idx != ultimo_quadro:
                ultimo_quadro = quadro_idx
                ultimo_texto  = texto_quadro
                falar(texto_quadro)

    except KeyboardInterrupt:
        print("Encerrando.")
        break
    except Exception as e:
        print("Erro: " + str(e))
        
    # Aciona movimento de cabeça ocioso se não falou nada recentemente e já passou algum tempo
    agora = time.time()
    if agora - tempo_ultimo_movimento > random.uniform(3, 7):
        mover_cabeca_idle()
        tempo_ultimo_movimento = agora

    time.sleep(1)  # poll a cada 1s — rápido o suficiente para pegar a troca de quadro
