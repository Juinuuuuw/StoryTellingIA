import urllib.request
import json
import time

url_init = "http://127.0.0.1:5000/iniciar_historia"
data_init = {
    "nome": "Eduardo",
    "tema": "Espaço",
    "skill": "katherine_johnson",
    "genero": "Masculino",
    "visual_fixo": "1boy, dark skin, short hair, brown eyes"
}
req_init = urllib.request.Request(url_init, data=json.dumps(data_init).encode('utf-8'), method="POST", headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req_init) as resp:
    res_init = json.loads(resp.read().decode('utf-8'))
    print("Init response keys:", res_init.keys())
    print("imagens_arquivos:", res_init.get("imagens_arquivos"))
