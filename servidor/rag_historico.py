"""
rag_historico.py — Recuperação de fatos históricos para enriquecer os prompts do LLM.

Estratégia: sem dependências externas.
1. Filtra fatos pelo personagem (NPC principal da cena).
2. Pontua: +10 se o step_id atual está na lista "steps" do fato, +1 por tag em comum com o goal.
3. Retorna os top-k fatos como texto pronto para injetar no prompt.
"""

import json
import os
from typing import List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BASE = os.path.join(BASE_DIR, "base_conhecimento.json")

_base_cache = None


def _carregar_base() -> dict:
    global _base_cache
    if _base_cache is None:
        try:
            with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
                _base_cache = json.load(f)
        except Exception as e:
            print(f"⚠️  RAG: Não foi possível carregar base_conhecimento.json: {e}")
            _base_cache = {}
    return _base_cache


def _normalizar_personagem(nome: str) -> str:
    """Mapeia o nome do NPC para a chave do JSON."""
    mapa = {
        "katherine johnson": "katherine_johnson",
        "katherine": "katherine_johnson",
        "alan turing": "alan_turing",
        "turing": "alan_turing",
        "steve jobs": "steve_jobs",
        "jobs": "steve_jobs",
        # Personagens da história_computacao fallback
        "charles babbage": "alan_turing",
        "ada lovelace": "alan_turing",
        "j.c.r. licklider": "alan_turing",
    }
    return mapa.get(nome.lower().strip(), "")


def buscar_fatos(npc_nome: str, step_id: str, goal: str = "", topk: int = 3) -> str:
    """
    Retorna os fatos históricos mais relevantes formatados como string
    pronta para injeção no system prompt do LLM.

    Args:
        npc_nome:  Nome do NPC principal da cena (ex: "Katherine Johnson").
        step_id:   ID do step atual (ex: "west_computing").
        goal:      Texto do objetivo da cena — usado para pontuar por tags.
        topk:      Quantidade máxima de fatos a retornar.

    Returns:
        String formatada com os fatos, ou string vazia se não encontrar nada.
    """
    base = _carregar_base()
    chave = _normalizar_personagem(npc_nome)

    if not chave or chave not in base:
        return ""

    fatos = base[chave]
    goal_lower = goal.lower()

    pontuados: List[tuple] = []
    for fato in fatos:
        score = 0

        # Correspondência direta de step (alta prioridade)
        if step_id in fato.get("steps", []):
            score += 10

        # Sobreposição de tags com o goal da cena
        for tag in fato.get("tags", []):
            if tag.lower() in goal_lower:
                score += 1

        pontuados.append((score, fato))

    # Ordena por pontuação (maior primeiro), depois por id para desempate estável
    pontuados.sort(key=lambda x: (-x[0], x[1]["id"]))

    selecionados = [f for score, f in pontuados if score > 0][:topk]

    if not selecionados:
        # Fallback: retorna os primeiros fatos gerais do personagem
        selecionados = fatos[:min(topk, len(fatos))]

    linhas = [f"- {f['fato']}" for f in selecionados]
    return "\n".join(linhas)
