"""
rembg_server.py — Microserviço de remoção de fundo para o StoryTellingIA
Roda na porta 5001 em paralelo com o servidor_ia.py (porta 5000).

Instalação: pip install rembg flask flask-cors pillow onnxruntime
Uso: python rembg_server.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import io
import os

app = Flask(__name__)
CORS(app)

# Carrega o modelo uma vez na inicialização (evita recarregar a cada request)
print("[*] Carregando modelo rembg (u2net)... aguarde.")
try:
    from rembg import remove, new_session
    SESSION = new_session("u2net")
    print("[+] Modelo rembg carregado com sucesso!")
except ImportError:
    SESSION = None
    print("[-] rembg nao instalado. Execute: pip install rembg onnxruntime")

@app.route('/rembg', methods=['POST'])
def remover_fundo():
    if SESSION is None:
        return jsonify({"erro": "rembg não instalado"}), 503

    dados = request.json
    if not dados or 'input_image' not in dados:
        return jsonify({"erro": "Campo 'input_image' (base64) obrigatório"}), 400

    try:
        # Decodifica a imagem base64 recebida
        img_bytes = base64.b64decode(dados['input_image'])
        img_input = io.BytesIO(img_bytes)

        # Remove o fundo
        from PIL import Image
        img_pil = Image.open(img_input).convert("RGBA")
        img_sem_fundo = remove(img_pil, session=SESSION)

        # Codifica o resultado de volta para base64
        buf = io.BytesIO()
        img_sem_fundo.save(buf, format="PNG")
        buf.seek(0)
        result_b64 = base64.b64encode(buf.read()).decode("utf-8")

        return jsonify({"image": result_b64})

    except Exception as e:
        print(f"[-] Erro no rembg: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "rembg_disponivel": SESSION is not None,
        "porta": 5001
    })

if __name__ == '__main__':
    print("[*] rembg_server rodando na porta 5001")
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
