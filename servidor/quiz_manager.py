import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz.db")


def init_db():
    """Cria as tabelas do banco de dados se não existirem."""
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS sessoes_quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            nome_aluno TEXT NOT NULL,
            tema TEXT NOT NULL,
            skill TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            total_perguntas INTEGER DEFAULT 0,
            acertos INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS perguntas_quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            ordem INTEGER NOT NULL,
            pergunta TEXT NOT NULL,
            opcoes TEXT NOT NULL,
            resposta_correta INTEGER NOT NULL,
            ato_referencia INTEGER DEFAULT 1,
            FOREIGN KEY (session_id) REFERENCES sessoes_quiz(session_id)
        );

        CREATE TABLE IF NOT EXISTS respostas_quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            pergunta_id INTEGER NOT NULL,
            resposta_dada INTEGER,
            deu_up INTEGER DEFAULT 0,
            correta INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessoes_quiz(session_id),
            FOREIGN KEY (pergunta_id) REFERENCES perguntas_quiz(id)
        );
    """)
    con.commit()
    con.close()
    print("✅ Quiz DB inicializado.")


def criar_sessao_quiz(session_id, nome_aluno, tema, skill):
    """Cria um registro de sessão de quiz no banco."""
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("""
            INSERT OR IGNORE INTO sessoes_quiz (session_id, nome_aluno, tema, skill, data_hora)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, nome_aluno, tema, skill, datetime.now().isoformat()))
        con.commit()
        print(f"📋 Sessão de quiz criada: {session_id} | Aluno: {nome_aluno}")
    finally:
        con.close()


def salvar_perguntas(session_id, perguntas):
    """
    Salva a lista de perguntas geradas pela IA no banco.
    Retorna uma lista de IDs dos registros criados.
    """
    con = sqlite3.connect(DB_PATH)
    ids = []
    try:
        for i, p in enumerate(perguntas):
            opcoes_json = json.dumps(p.get("opcoes", []), ensure_ascii=False)
            cur = con.execute("""
                INSERT INTO perguntas_quiz (session_id, ordem, pergunta, opcoes, resposta_correta, ato_referencia)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                i,
                p.get("pergunta", ""),
                opcoes_json,
                p.get("resposta_correta", 0),
                p.get("ato", 1)
            ))
            ids.append(cur.lastrowid)

        # Atualiza o total de perguntas na sessão
        con.execute("""
            UPDATE sessoes_quiz SET total_perguntas = ? WHERE session_id = ?
        """, (len(perguntas), session_id))

        con.commit()
        print(f"❓ {len(perguntas)} pergunta(s) salvas para sessão {session_id}")
    finally:
        con.close()
    return ids


def salvar_resposta(session_id, pergunta_id, resposta_idx, correta, deu_up=False):
    """Salva a resposta do aluno para uma pergunta específica."""
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("""
            INSERT INTO respostas_quiz (session_id, pergunta_id, resposta_dada, deu_up, correta, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            pergunta_id,
            resposta_idx,
            1 if deu_up else 0,
            1 if correta else 0,
            datetime.now().isoformat()
        ))

        # Atualiza acertos na sessão
        if correta:
            con.execute("""
                UPDATE sessoes_quiz SET acertos = acertos + 1 WHERE session_id = ?
            """, (session_id,))

        con.commit()
        status = "✅ CORRETA" if correta else ("🤷 DEU UP" if deu_up else "❌ ERRADA")
        print(f"💾 Resposta salva | Pergunta {pergunta_id} | {status}")
    finally:
        con.close()


def get_ids_perguntas(session_id):
    """Retorna a lista de IDs das perguntas de uma sessão, em ordem."""
    con = sqlite3.connect(DB_PATH)
    try:
        rows = con.execute("""
            SELECT id FROM perguntas_quiz WHERE session_id = ? ORDER BY ordem ASC
        """, (session_id,)).fetchall()
        return [r[0] for r in rows]
    finally:
        con.close()


def get_resultado_sessao(session_id):
    """Retorna um dicionário com o resultado completo de uma sessão."""
    con = sqlite3.connect(DB_PATH)
    try:
        sessao = con.execute("""
            SELECT nome_aluno, tema, skill, data_hora, total_perguntas, acertos
            FROM sessoes_quiz WHERE session_id = ?
        """, (session_id,)).fetchone()

        if not sessao:
            return None

        perguntas_rows = con.execute("""
            SELECT pq.id, pq.ordem, pq.pergunta, pq.opcoes, pq.resposta_correta, pq.ato_referencia,
                   rq.resposta_dada, rq.deu_up, rq.correta
            FROM perguntas_quiz pq
            LEFT JOIN respostas_quiz rq ON pq.id = rq.pergunta_id
            WHERE pq.session_id = ?
            ORDER BY pq.ordem ASC
        """, (session_id,)).fetchall()

        perguntas = []
        for row in perguntas_rows:
            opcoes = json.loads(row[3])
            perguntas.append({
                "id": row[0],
                "ordem": row[1],
                "pergunta": row[2],
                "opcoes": opcoes,
                "resposta_correta": row[4],
                "ato": row[5],
                "resposta_dada": row[6],
                "deu_up": bool(row[7]),
                "correta": bool(row[8])
            })

        return {
            "session_id": session_id,
            "nome_aluno": sessao[0],
            "tema": sessao[1],
            "skill": sessao[2],
            "data_hora": sessao[3],
            "total_perguntas": sessao[4],
            "acertos": sessao[5],
            "percentual": round((sessao[5] / sessao[4]) * 100) if sessao[4] > 0 else 0,
            "perguntas": perguntas
        }
    finally:
        con.close()


def get_resultado_geral():
    """Retorna um sumário agregado de todas as sessões."""
    con = sqlite3.connect(DB_PATH)
    try:
        sessoes = con.execute("""
            SELECT session_id, nome_aluno, tema, skill, data_hora, total_perguntas, acertos
            FROM sessoes_quiz
            ORDER BY data_hora DESC
        """).fetchall()

        total_sessoes = len(sessoes)
        total_respostas = sum(s[5] for s in sessoes)
        total_acertos = sum(s[6] for s in sessoes)

        return {
            "total_sessoes": total_sessoes,
            "total_perguntas_respondidas": total_respostas,
            "total_acertos": total_acertos,
            "percentual_geral": round((total_acertos / total_respostas) * 100) if total_respostas > 0 else 0,
            "sessoes": [
                {
                    "session_id": s[0],
                    "nome_aluno": s[1],
                    "tema": s[2],
                    "skill": s[3],
                    "data_hora": s[4],
                    "total_perguntas": s[5],
                    "acertos": s[6],
                    "percentual": round((s[6] / s[5]) * 100) if s[5] > 0 else 0
                }
                for s in sessoes
            ]
        }
    finally:
        con.close()
