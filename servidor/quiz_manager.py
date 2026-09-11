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

        CREATE TABLE IF NOT EXISTS sessoes_historia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            nome_aluno TEXT NOT NULL,
            tema TEXT NOT NULL,
            skill TEXT NOT NULL,
            genero TEXT DEFAULT 'Masculino',
            data_inicio TEXT NOT NULL,
            data_fim TEXT,
            total_cenas INTEGER DEFAULT 0,
            status TEXT DEFAULT 'em_andamento'
        );

        CREATE TABLE IF NOT EXISTS cenas_historia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            ordem INTEGER NOT NULL,
            step_id TEXT NOT NULL,
            ato INTEGER DEFAULT 1,
            npc_principal TEXT,
            narrativa TEXT NOT NULL,
            opcoes TEXT NOT NULL,
            escolha_feita TEXT,
            timestamp_cena TEXT NOT NULL,
            timestamp_escolha TEXT,
            FOREIGN KEY (session_id) REFERENCES sessoes_historia(session_id)
        );

        CREATE TABLE IF NOT EXISTS respostas_likert (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            secao_id INTEGER NOT NULL,
            secao_nome TEXT NOT NULL,
            pergunta_ref TEXT NOT NULL,
            pergunta_texto TEXT NOT NULL,
            resposta INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        );

        -- ── PRÉ-QUESTIONÁRIO ─────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS pre_questionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pre_id TEXT NOT NULL UNIQUE,
            data_hora TEXT NOT NULL,
            tempo_resposta_seg INTEGER DEFAULT 0,
            idade INTEGER,
            area_formacao TEXT,
            contato_robos TEXT,
            frequencia_ia TEXT,
            conhecimento_historia_pre INTEGER,
            ja_ouviu_marco_pre TEXT,
            conhecimento_turing_pre INTEGER,
            ja_ouviu_marco_historico TEXT,
            percepcao_nao TEXT,
            expectativa_experiencia TEXT,
            status TEXT DEFAULT 'aguardando_historia',
            session_id TEXT
        );

        -- ── MÉTRICAS DE TEMPO POR FASE ────────────────────────────────
        CREATE TABLE IF NOT EXISTS metricas_tempo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pre_id TEXT NOT NULL,
            fase TEXT NOT NULL,
            inicio TEXT NOT NULL,
            fim TEXT,
            duracao_seg INTEGER
        );
    """)
    con.commit()
    con.close()
    print("[OK] Quiz DB inicializado.")


# ─────────────────────────────────────────────────────────────
# PRÉ-QUESTIONÁRIO
# ─────────────────────────────────────────────────────────────

def _proximo_pre_id():
    """Gera o próximo ID sequencial (Q1, Q2, ...) de forma thread-safe."""
    con = sqlite3.connect(DB_PATH)
    try:
        row = con.execute("SELECT COUNT(*) FROM pre_questionarios").fetchone()
        next_num = (row[0] or 0) + 1
        return f"Q{next_num}"
    finally:
        con.close()


def salvar_pre_questionario(dados: dict) -> str:
    """Salva as respostas do pré-questionário. Retorna o pre_id gerado (ex: 'Q1')."""
    con = sqlite3.connect(DB_PATH)
    try:
        pre_id = _proximo_pre_id()
        percepcao_json = json.dumps(dados.get("percepcao_nao", {}), ensure_ascii=False)
        con.execute("""
            INSERT INTO pre_questionarios
                (pre_id, data_hora, tempo_resposta_seg,
                 idade, area_formacao, contato_robos, frequencia_ia,
                 conhecimento_historia_pre, ja_ouviu_marco_pre,
                 conhecimento_turing_pre, ja_ouviu_marco_historico,
                 percepcao_nao, expectativa_experiencia, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'aguardando_historia')
        """, (
            pre_id,
            datetime.now().isoformat(),
            dados.get("tempo_resposta_seg", 0),
            dados.get("idade"),
            dados.get("area_formacao"),
            dados.get("contato_robos"),
            dados.get("frequencia_ia"),
            dados.get("conhecimento_historia_pre"),
            dados.get("ja_ouviu_marco_pre"),
            dados.get("conhecimento_turing_pre"),
            dados.get("ja_ouviu_marco_historico"),
            percepcao_json,
            dados.get("expectativa_experiencia"),
        ))
        con.commit()
        print(f"[OK] Pre-questionario salvo: {pre_id}")
        return pre_id
    finally:
        con.close()


def atualizar_status_pre(pre_id: str, novo_status: str, session_id: str = None):
    """Atualiza o status e/ou session_id de um participante."""
    con = sqlite3.connect(DB_PATH)
    try:
        if session_id:
            con.execute(
                "UPDATE pre_questionarios SET status=?, session_id=? WHERE pre_id=?",
                (novo_status, session_id, pre_id)
            )
        else:
            con.execute(
                "UPDATE pre_questionarios SET status=? WHERE pre_id=?",
                (novo_status, pre_id)
            )
        con.commit()
        print(f"[UPDATE] Status do participante {pre_id} -> {novo_status}")
    finally:
        con.close()


def get_pre_questionario(pre_id: str):
    """Retorna os dados de um pré-questionário pelo pre_id."""
    con = sqlite3.connect(DB_PATH)
    try:
        row = con.execute("""
            SELECT pre_id, data_hora, tempo_resposta_seg,
                   idade, area_formacao, contato_robos, frequencia_ia,
                   conhecimento_historia_pre, ja_ouviu_marco_pre,
                   conhecimento_turing_pre, ja_ouviu_marco_historico,
                   percepcao_nao, expectativa_experiencia, status, session_id
            FROM pre_questionarios WHERE pre_id=?
        """, (pre_id,)).fetchone()
        if not row:
            return None
        percepcao = {}
        try:
            percepcao = json.loads(row[11]) if row[11] else {}
        except Exception:
            pass
        return {
            "pre_id": row[0], "data_hora": row[1],
            "tempo_resposta_seg": row[2], "idade": row[3],
            "area_formacao": row[4], "contato_robos": row[5],
            "frequencia_ia": row[6], "conhecimento_historia_pre": row[7],
            "ja_ouviu_marco_pre": row[8], "conhecimento_turing_pre": row[9],
            "ja_ouviu_marco_historico": row[10], "percepcao_nao": percepcao,
            "expectativa_experiencia": row[12], "status": row[13],
            "session_id": row[14],
        }
    finally:
        con.close()


def get_fila_pre_questionarios():
    """Retorna lista de todos os participantes para o dashboard."""
    con = sqlite3.connect(DB_PATH)
    try:
        rows = con.execute("""
            SELECT pre_id, data_hora, status, session_id
            FROM pre_questionarios
            ORDER BY data_hora DESC
        """).fetchall()
        return [
            {"pre_id": r[0], "data_hora": r[1], "status": r[2], "session_id": r[3]}
            for r in rows
        ]
    finally:
        con.close()


def get_todos_pre_questionarios():
    """Retorna todos os pré-questionários para exportação."""
    con = sqlite3.connect(DB_PATH)
    try:
        rows = con.execute("""
            SELECT pre_id, data_hora, tempo_resposta_seg,
                   idade, area_formacao, contato_robos, frequencia_ia,
                   conhecimento_historia_pre, ja_ouviu_marco_pre,
                   conhecimento_turing_pre, ja_ouviu_marco_historico,
                   percepcao_nao, expectativa_experiencia, status, session_id
            FROM pre_questionarios ORDER BY data_hora ASC
        """).fetchall()
        result = []
        for row in rows:
            percepcao = {}
            try:
                percepcao = json.loads(row[11]) if row[11] else {}
            except Exception:
                pass
            result.append({
                "pre_id": row[0], "data_hora": row[1],
                "tempo_resposta_seg": row[2], "idade": row[3],
                "area_formacao": row[4], "contato_robos": row[5],
                "frequencia_ia": row[6], "conhecimento_historia_pre": row[7],
                "ja_ouviu_marco_pre": row[8], "conhecimento_turing_pre": row[9],
                "ja_ouviu_marco_historico": row[10], "percepcao_nao": percepcao,
                "expectativa_experiencia": row[12], "status": row[13],
                "session_id": row[14],
            })
        return result
    finally:
        con.close()


def get_estatisticas_participacao():
    """Retorna métricas agregadas de participação para o dashboard."""
    con = sqlite3.connect(DB_PATH)
    try:
        total_pre = con.execute("SELECT COUNT(*) FROM pre_questionarios").fetchone()[0]
        total_historia = con.execute(
            "SELECT COUNT(*) FROM pre_questionarios WHERE status IN ('em_historia','historia_concluida','pos_respondido')"
        ).fetchone()[0]
        total_pos = con.execute(
            "SELECT COUNT(*) FROM pre_questionarios WHERE status='pos_respondido'"
        ).fetchone()[0]
        total_desistiu = con.execute(
            "SELECT COUNT(*) FROM pre_questionarios WHERE status='desistiu'"
        ).fetchone()[0]
        aguardando = con.execute(
            "SELECT COUNT(*) FROM pre_questionarios WHERE status='aguardando_historia'"
        ).fetchone()[0]
        return {
            "total_pre": total_pre,
            "total_historia": total_historia,
            "total_pos": total_pos,
            "total_desistiu": total_desistiu,
            "aguardando_historia": aguardando,
        }
    finally:
        con.close()


def registrar_metrica_tempo(pre_id: str, fase: str, inicio: str, fim: str = None, duracao_seg: int = None):
    """Registra ou atualiza uma métrica de tempo para uma fase específica."""
    con = sqlite3.connect(DB_PATH)
    try:
        existing = con.execute(
            "SELECT id FROM metricas_tempo WHERE pre_id=? AND fase=?",
            (pre_id, fase)
        ).fetchone()
        if existing:
            con.execute(
                "UPDATE metricas_tempo SET fim=?, duracao_seg=? WHERE pre_id=? AND fase=?",
                (fim, duracao_seg, pre_id, fase)
            )
        else:
            con.execute(
                "INSERT INTO metricas_tempo (pre_id, fase, inicio, fim, duracao_seg) VALUES (?, ?, ?, ?, ?)",
                (pre_id, fase, inicio, fim, duracao_seg)
            )
        con.commit()
    finally:
        con.close()


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


def exportar_excel_geral(caminho_arquivo):
    """
    Gera um arquivo .xlsx focado no estudo do quiz pós-sessão, com 4 abas:
    - 'Resumo Sessoes': uma linha por sessão com desempenho geral
    - 'Quiz Detalhado': FOCO PRINCIPAL — uma linha por resposta com texto completo das opções,
      resposta escolhida, se acertou, se desistiu, e o ato da história relacionado
    - 'Por Aluno': desempenho agregado por aluno (para análise entre sessões)
    - 'Historia': cenas e escolhas feitas durante a narrativa (contexto)
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise ImportError("openpyxl não instalado. Execute: pip install openpyxl")

    AZUL_HEADER  = "1F3864"
    VERDE_HEADER = "1E5C3A"
    ROXO_HEADER  = "3D1A5C"
    CINZA_HEADER = "3C3C3C"
    COR_CORRETA  = "C6EFCE"  # verde claro
    COR_ERRADA   = "FFCCCC"  # vermelho claro
    COR_DESIST   = "FFEB9C"  # amarelo claro

    def estilizar_header(ws, headers, cor_hex):
        ws.append(headers)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = Font(bold=True, color="FFFFFF", size=11)
            cell.fill = PatternFill(start_color=cor_hex, end_color=cor_hex, fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.row_dimensions[1].height = 30

    def auto_width(ws, max_col_width=70):
        for col in ws.columns:
            vals = [str(cell.value or "") for cell in col]
            w = max(len(v) for v in vals) if vals else 10
            ws.column_dimensions[get_column_letter(col[0].column)].width = max(10, min(w + 2, max_col_width))

    def colorir_linha(ws, row_num, cor_hex):
        for cell in ws[row_num]:
            cell.fill = PatternFill(start_color=cor_hex, end_color=cor_hex, fill_type="solid")

    wb = openpyxl.Workbook()
    LETRAS = ["A", "B", "C", "D"]

    con = sqlite3.connect(DB_PATH)
    try:
        # ══════════════════════════════════════════════════════
        # ABA 1 — RESUMO SESSÕES
        # ══════════════════════════════════════════════════════
        ws1 = wb.active
        ws1.title = "Resumo Sessoes"
        h1 = ["Sessao ID", "Aluno", "Tema", "Skill", "Data/Hora", "Total Perguntas",
              "Acertos", "Erros", "Desistencias", "% Acerto", "Situacao"]
        estilizar_header(ws1, h1, AZUL_HEADER)

        sessoes = con.execute("""
            SELECT sq.session_id, sq.nome_aluno, sq.tema, sq.skill, sq.data_hora,
                   sq.total_perguntas, sq.acertos
            FROM sessoes_quiz sq
            ORDER BY sq.data_hora DESC
        """).fetchall()

        for s in sessoes:
            sid, aluno, tema, skill, dt, total, acertos = s
            # Conta desistências
            desist = con.execute("""
                SELECT COUNT(*) FROM respostas_quiz
                WHERE session_id = ? AND deu_up = 1
            """, (sid,)).fetchone()[0]
            erros = total - acertos - desist
            pct = round((acertos / total) * 100) if total > 0 else 0
            situacao = "Excelente" if pct >= 80 else ("Satisfatorio" if pct >= 60 else ("Regular" if pct >= 40 else "Abaixo do esperado"))
            row_num = ws1.max_row + 1
            ws1.append([sid, aluno, tema, skill, dt, total, acertos, max(0,erros), desist, pct, situacao])
            # Cor por desempenho
            if pct >= 80:
                colorir_linha(ws1, row_num, COR_CORRETA)
            elif pct < 40:
                colorir_linha(ws1, row_num, COR_ERRADA)

        auto_width(ws1)

        # ══════════════════════════════════════════════════════
        # ABA 2 — QUIZ DETALHADO (FOCO DO ESTUDO)
        # ══════════════════════════════════════════════════════
        ws2 = wb.create_sheet("Quiz Detalhado")
        h2 = [
            "Aluno", "Tema", "Skill", "Data/Hora Sessao",
            "N Pergunta", "Ato Referencia", "Texto da Pergunta",
            "Opcao A", "Opcao B", "Opcao C", "Opcao D (Nao Lembro)",
            "Resposta Correta (letra)", "Resposta Correta (texto)",
            "Resposta do Aluno (letra)", "Resposta do Aluno (texto)",
            "Acertou", "Desistiu", "Hora da Resposta"
        ]
        estilizar_header(ws2, h2, VERDE_HEADER)

        rows = con.execute("""
            SELECT sq.nome_aluno, sq.tema, sq.skill, sq.data_hora,
                   pq.ordem, pq.ato_referencia, pq.pergunta, pq.opcoes, pq.resposta_correta,
                   rq.resposta_dada, rq.correta, rq.deu_up, rq.timestamp
            FROM sessoes_quiz sq
            JOIN perguntas_quiz pq ON sq.session_id = pq.session_id
            LEFT JOIN respostas_quiz rq ON pq.id = rq.pergunta_id
            ORDER BY sq.data_hora DESC, pq.ordem ASC
        """).fetchall()

        for r in rows:
            aluno, tema, skill, dt_sessao, ordem, ato, pergunta, opcoes_json, resp_correta_idx, resp_dada_idx, correta, deu_up, ts_resp = r
            try:
                opcoes = json.loads(opcoes_json)
            except:
                opcoes = []

            opc_a    = opcoes[0] if len(opcoes) > 0 else ""
            opc_b    = opcoes[1] if len(opcoes) > 1 else ""
            opc_c    = opcoes[2] if len(opcoes) > 2 else ""
            opc_d    = opcoes[3] if len(opcoes) > 3 else "Nao me lembro"

            correta_letra = LETRAS[resp_correta_idx] if resp_correta_idx is not None and 0 <= resp_correta_idx < 4 else "-"
            correta_texto = opcoes[resp_correta_idx] if resp_correta_idx is not None and 0 <= resp_correta_idx < len(opcoes) else "-"

            dada_letra    = LETRAS[resp_dada_idx] if resp_dada_idx is not None and 0 <= resp_dada_idx < 4 else "(nao respondeu)"
            dada_texto    = opcoes[resp_dada_idx] if resp_dada_idx is not None and 0 <= resp_dada_idx < len(opcoes) else "(nao respondeu)"

            acertou_str  = "Sim" if correta else "Nao"
            desistiu_str = "Sim" if deu_up else "Nao"

            row_num = ws2.max_row + 1
            ws2.append([
                aluno, tema, skill, dt_sessao,
                ordem + 1, ato, pergunta,
                opc_a, opc_b, opc_c, opc_d,
                correta_letra, correta_texto,
                dada_letra, dada_texto,
                acertou_str, desistiu_str, ts_resp or ""
            ])

            # Cor por resultado
            if deu_up:
                colorir_linha(ws2, row_num, COR_DESIST)
            elif correta:
                colorir_linha(ws2, row_num, COR_CORRETA)
            elif resp_dada_idx is not None:
                colorir_linha(ws2, row_num, COR_ERRADA)

        auto_width(ws2)

        # ══════════════════════════════════════════════════════
        # ABA 3 — RESUMO POR ALUNO (AGREGADO)
        # ══════════════════════════════════════════════════════
        ws3 = wb.create_sheet("Por Aluno")
        h3 = ["Aluno", "Sessoes", "Total Perguntas", "Acertos", "Desistencias",
              "% Acerto Geral", "Melhor Sessao (%)", "Pior Sessao (%)", "Temas Visitados"]
        estilizar_header(ws3, h3, ROXO_HEADER)

        alunos_agg = con.execute("""
            SELECT nome_aluno,
                   COUNT(DISTINCT session_id) as sessoes,
                   SUM(total_perguntas) as total_q,
                   SUM(acertos) as total_a,
                   MAX(ROUND(CAST(acertos AS FLOAT)/NULLIF(total_perguntas,0)*100)) as melhor,
                   MIN(ROUND(CAST(acertos AS FLOAT)/NULLIF(total_perguntas,0)*100)) as pior,
                   GROUP_CONCAT(DISTINCT tema) as temas
            FROM sessoes_quiz
            GROUP BY nome_aluno
            ORDER BY nome_aluno
        """).fetchall()

        for a in alunos_agg:
            aluno, sessoes, total_q, total_a, melhor, pior, temas_str = a
            desist_total = con.execute("""
                SELECT COUNT(*) FROM respostas_quiz rq
                JOIN sessoes_quiz sq ON rq.session_id = sq.session_id
                WHERE sq.nome_aluno = ? AND rq.deu_up = 1
            """, (aluno,)).fetchone()[0]
            pct_geral = round((total_a / total_q) * 100) if total_q else 0
            row_num = ws3.max_row + 1
            ws3.append([aluno, sessoes, total_q, total_a, desist_total,
                        pct_geral, melhor or 0, pior or 0, temas_str or ""])
            if pct_geral >= 80:
                colorir_linha(ws3, row_num, COR_CORRETA)
            elif pct_geral < 40:
                colorir_linha(ws3, row_num, COR_ERRADA)

        auto_width(ws3)

        # ══════════════════════════════════════════════════════
        # ABA 4 — HISTORIA (CONTEXTO)
        # ══════════════════════════════════════════════════════
        ws4 = wb.create_sheet("Historia")
        h4 = ["Aluno", "Skill", "Tema", "Inicio", "Fim", "Status",
              "Cena N", "Ato", "Step", "NPC", "Narrativa (resumo)", "Opcoes", "Escolha Feita"]
        estilizar_header(ws4, h4, CINZA_HEADER)

        cenas = con.execute("""
            SELECT sh.nome_aluno, sh.skill, sh.tema, sh.data_inicio, sh.data_fim, sh.status,
                   ch.ordem, ch.ato, ch.step_id, ch.npc_principal,
                   ch.narrativa, ch.opcoes, ch.escolha_feita
            FROM sessoes_historia sh
            JOIN cenas_historia ch ON sh.session_id = ch.session_id
            ORDER BY sh.data_inicio DESC, ch.ordem ASC
        """).fetchall()

        for c in cenas:
            aluno, skill, tema, inicio, fim, status, ordem, ato, step_id, npc, narrativa, opcoes_json, escolha = c
            try:
                opcoes_lista = json.loads(opcoes_json)
                opcoes_str = " | ".join(opcoes_lista)
            except:
                opcoes_str = opcoes_json or ""
            narrativa_resumo = (narrativa or "")[:300] + ("..." if len(narrativa or "") > 300 else "")
            ws4.append([aluno, skill, tema, inicio, fim, status,
                        ordem + 1, ato, step_id, npc, narrativa_resumo, opcoes_str, escolha or "(aguardando)"])

        auto_width(ws4, max_col_width=80)
        # ══════════════════════════════════════════════════════
        # ABA 5 — QUESTIONÁRIO LIKERT (ESTUDO PÓS-SESSÃO)
        # ══════════════════════════════════════════════════════
        ws5 = wb.create_sheet("Likert Pos")
        h5 = ["Sessao", "Aluno", "Tema", "Skill", "Secao", "Nome da Secao", "Ref", "Pergunta/Enunciado", "Resposta (1-5)", "Hora da Resposta"]
        estilizar_header(ws5, h5, "8B0000")

        likert_rows = con.execute('''
            SELECT sq.session_id, sq.nome_aluno, sq.tema, sq.skill,
                   rl.secao_id, rl.secao_nome, rl.pergunta_ref, rl.pergunta_texto, rl.resposta, rl.timestamp
            FROM respostas_likert rl
            JOIN sessoes_quiz sq ON sq.session_id = rl.session_id
            ORDER BY sq.data_hora DESC, rl.secao_id ASC, rl.id ASC
        ''').fetchall()

        for r in likert_rows:
            ws5.append([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]])
            
        auto_width(ws5, max_col_width=100)

        # ══════════════════════════════════════════════════════
        # ABA 6 — PRÉ-QUESTIONÁRIO
        # ══════════════════════════════════════════════════════
        ws6 = wb.create_sheet("Pre Quest")
        h6 = [
            "ID (pre_id)", "Data/Hora", "Tempo Resposta (seg)",
            "Idade", "Area de Formacao/Atuacao",
            "Contato Anterior com Robos Sociais", "Frequencia uso IA Generativa",
            "Conhecimento Historia Comp. Pre (1-5)", "Ja ouviu falar de marco historico Pre",
            "Conhecimento Alan Turing Pre (1-5)", "Ja ouviu falar de marco historico (2)",
            # Percepção NAO — Antropomorfismo
            "NAO: Falso/Natural", "NAO: Mecanico/Humano", "NAO: Inconsciente/Consciente",
            "NAO: Artificial/Realista (Antrop)", "NAO: Move rigidez/fluidez",
            # Animacidade
            "NAO: Morto/Com vida", "NAO: Parado/Energico", "NAO: Artificial/Realista (Anim)",
            "NAO: Estatico/Interativo", "NAO: Apatico/Participativo",
            # Simpatia
            "NAO: Nao gosto/Gosto", "NAO: Hostil/Amigavel", "NAO: Antipatico/Gentil",
            "NAO: Desagradavel/Agradavel", "NAO: Horrivel/Simpatico",
            # Inteligência
            "NAO: Incompetente/Competente", "NAO: Ignorante/Sabedor",
            "NAO: Pouco inteligente/Inteligente", "NAO: Insensato/Sensato",
            # Segurança
            "NAO: Ansioso/Descontraido", "NAO: Calmo/Agitado", "NAO: Sereno/Surpreendido",
            # Expectativa e status
            "Expectativa sobre a experiencia",
            "Status Participacao", "Session ID Vinculado"
        ]
        estilizar_header(ws6, h6, "1A5276")

        pre_rows = con.execute("""
            SELECT pre_id, data_hora, tempo_resposta_seg,
                   idade, area_formacao, contato_robos, frequencia_ia,
                   conhecimento_historia_pre, ja_ouviu_marco_pre,
                   conhecimento_turing_pre, ja_ouviu_marco_historico,
                   percepcao_nao, expectativa_experiencia, status, session_id
            FROM pre_questionarios ORDER BY data_hora ASC
        """).fetchall()

        # Mapeamento das chaves de percepção do NAO para as colunas do Excel
        # As chaves correspondem às seções e itens do questionário
        PERCEPCAO_KEYS = [
            # Antropomorfismo
            "s0_g0_l0", "s0_g0_l1", "s0_g0_l2", "s0_g0_l3", "s0_g0_l4",
            # Animacidade
            "s0_g1_l0", "s0_g1_l1", "s0_g1_l2", "s0_g1_l3", "s0_g1_l4",
            # Simpatia
            "s0_g2_l0", "s0_g2_l1", "s0_g2_l2", "s0_g2_l3", "s0_g2_l4",
            # Inteligência
            "s0_g3_l0", "s0_g3_l1", "s0_g3_l2", "s0_g3_l3",
            # Segurança
            "s0_g4_l0", "s0_g4_l1", "s0_g4_l2",
        ]

        for r in pre_rows:
            pre_id, dt, tempo, idade, area, contato, freq_ia, \
            conhec_hist, marco_pre, conhec_turing, marco_hist, \
            percepcao_json, expectativa, status_p, sid = r

            percepcao = {}
            try:
                percepcao = json.loads(percepcao_json) if percepcao_json else {}
            except Exception:
                pass

            percepcao_vals = [percepcao.get(k, "") for k in PERCEPCAO_KEYS]

            row_data = [
                pre_id, dt, tempo, idade, area, contato, freq_ia,
                conhec_hist, marco_pre, conhec_turing, marco_hist,
                *percepcao_vals,
                expectativa, status_p, sid or ""
            ]
            ws6.append(row_data)

        auto_width(ws6, max_col_width=50)

        # ══════════════════════════════════════════════════════
        # ABA 7 — FUNIL DE PARTICIPAÇÃO
        # ══════════════════════════════════════════════════════
        ws7 = wb.create_sheet("Participacao")
        h7 = ["ID (pre_id)", "Data/Hora Pre Quest", "Status", "Session ID",
              "Respondeu Pre", "Fez Historia", "Respondeu Pos", "Desistiu Sem Historia"]
        estilizar_header(ws7, h7, "145A32")

        for r in pre_rows:
            pre_id, dt, _tempo = r[0], r[1], r[2]
            status_p, sid = r[13], r[14]
            respondeu_pre = "Sim"
            fez_historia = "Sim" if status_p in ("em_historia", "historia_concluida", "pos_respondido") else "Nao"
            respondeu_pos = "Sim" if status_p == "pos_respondido" else "Nao"
            desistiu = "Sim" if status_p == "desistiu" else "Nao"
            ws7.append([pre_id, dt, status_p, sid or "", respondeu_pre, fez_historia, respondeu_pos, desistiu])
            # Colorir por status
            row_num = ws7.max_row
            if status_p == "pos_respondido":
                colorir_linha(ws7, row_num, COR_CORRETA)
            elif status_p == "desistiu":
                colorir_linha(ws7, row_num, COR_ERRADA)
            elif status_p == "aguardando_historia":
                colorir_linha(ws7, row_num, COR_DESIST)

        auto_width(ws7, max_col_width=50)

    finally:
        con.close()

    wb.save(caminho_arquivo)
    print(f"📊 Excel exportado para: {caminho_arquivo}")



def criar_sessao_historia(session_id, nome_aluno, tema, skill, genero='Masculino'):
    """Registra o início de uma sessão de história."""
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("""
            INSERT OR IGNORE INTO sessoes_historia
                (session_id, nome_aluno, tema, skill, genero, data_inicio)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, nome_aluno, tema, skill, genero, datetime.now().isoformat()))
        con.commit()
        print(f"📖 Sessão de história criada: {session_id} | {nome_aluno}")
    finally:
        con.close()


def salvar_cena(session_id, ordem, step_id, ato, npc_principal, narrativa, opcoes):
    """
    Salva uma cena gerada pela IA.
    Retorna o id do registro criado.
    """
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.execute("""
            INSERT INTO cenas_historia
                (session_id, ordem, step_id, ato, npc_principal, narrativa, opcoes, timestamp_cena)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, ordem, step_id, ato, npc_principal,
            narrativa,
            json.dumps(opcoes, ensure_ascii=False),
            datetime.now().isoformat()
        ))
        cena_id = cur.lastrowid
        con.execute("""
            UPDATE sessoes_historia SET total_cenas = total_cenas + 1 WHERE session_id = ?
        """, (session_id,))
        con.commit()
        print(f"🎬 Cena {ordem} salva (step: {step_id}) | sessão {session_id}")
        return cena_id
    finally:
        con.close()


def registrar_escolha(session_id, ordem_cena, escolha_texto):
    """Registra a escolha que o aluno fez em uma cena específica."""
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("""
            UPDATE cenas_historia
            SET escolha_feita = ?, timestamp_escolha = ?
            WHERE session_id = ? AND ordem = ?
        """, (escolha_texto, datetime.now().isoformat(), session_id, ordem_cena))
        con.commit()
        print(f"✅ Escolha registrada na cena {ordem_cena}: '{escolha_texto}'")
    finally:
        con.close()


def finalizar_sessao_historia(session_id):
    """Marca a sessão de história como concluída."""
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("""
            UPDATE sessoes_historia SET status = 'concluida', data_fim = ? WHERE session_id = ?
        """, (datetime.now().isoformat(), session_id))
        con.commit()
        print(f"🏁 Sessão de história finalizada: {session_id}")
    finally:
        con.close()


def get_historia_completa(session_id):
    """Retorna a sessão de história com todas as cenas e escolhas."""
    con = sqlite3.connect(DB_PATH)
    try:
        row = con.execute("""
            SELECT session_id, nome_aluno, tema, skill, genero, data_inicio, data_fim, total_cenas, status
            FROM sessoes_historia WHERE session_id = ?
        """, (session_id,)).fetchone()
        if not row:
            return None

        cenas_rows = con.execute("""
            SELECT id, ordem, step_id, ato, npc_principal, narrativa, opcoes, escolha_feita,
                   timestamp_cena, timestamp_escolha
            FROM cenas_historia WHERE session_id = ? ORDER BY ordem ASC
        """, (session_id,)).fetchall()

        cenas = []
        for c in cenas_rows:
            try:
                opcoes = json.loads(c[6])
            except:
                opcoes = []
            cenas.append({
                'id': c[0], 'ordem': c[1], 'step_id': c[2], 'ato': c[3],
                'npc_principal': c[4], 'narrativa': c[5],
                'opcoes': opcoes, 'escolha_feita': c[7],
                'timestamp_cena': c[8], 'timestamp_escolha': c[9]
            })

        return {
            'session_id': row[0], 'nome_aluno': row[1], 'tema': row[2],
            'skill': row[3], 'genero': row[4], 'data_inicio': row[5],
            'data_fim': row[6], 'total_cenas': row[7], 'status': row[8],
            'cenas': cenas
        }
    finally:
        con.close()


def get_historias_geral():
    """Lista todas as sessões de história em resumo."""
    con = sqlite3.connect(DB_PATH)
    try:
        rows = con.execute("""
            SELECT session_id, nome_aluno, tema, skill, genero, data_inicio, data_fim, total_cenas, status
            FROM sessoes_historia ORDER BY data_inicio DESC
        """).fetchall()
        return [{
            'session_id': r[0], 'nome_aluno': r[1], 'tema': r[2],
            'skill': r[3], 'genero': r[4], 'data_inicio': r[5],
            'data_fim': r[6], 'total_cenas': r[7], 'status': r[8]
        } for r in rows]
    finally:
        con.close()



# ─────────────────────────────────────────────────────────────
# PERSISTÊNCIA DO QUESTIONÁRIO LIKERT (ESTUDO PÓS-SESSÃO)
# ─────────────────────────────────────────────────────────────

def salvar_likert(session_id, secoes, respostas):
    """Salva as respostas do questionário Likert pós-sessão."""
    con = sqlite3.connect(DB_PATH)
    try:
        now = datetime.now().isoformat()
        
        for s_idx, secao in enumerate(secoes):
            s_id = s_idx + 1
            s_nome = secao.get('titulo', f'Secao {s_id}')
            
            if secao.get('tipo') == 'escala':
                for q_idx, perg in enumerate(secao.get('perguntas', [])):
                    ref = f's{s_idx}_q{q_idx}'
                    if ref in respostas:
                        val = respostas[ref]
                        texto = perg.get('texto', '')
                        con.execute("""
                            INSERT INTO respostas_likert (session_id, secao_id, secao_nome, pergunta_ref, pergunta_texto, resposta, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (session_id, s_id, s_nome, ref, texto, val, now))
            
            elif secao.get('tipo') == 'grid':
                for g_idx, grupo in enumerate(secao.get('grupos', [])):
                    subt = grupo.get('subtitulo', '')
                    for l_idx, linha in enumerate(grupo.get('linhas', [])):
                        ref = f's{s_idx}_g{g_idx}_l{l_idx}'
                        if ref in respostas:
                            val = respostas[ref]
                            texto = f'{subt} - {linha}'
                            con.execute("""
                                INSERT INTO respostas_likert (session_id, secao_id, secao_nome, pergunta_ref, pergunta_texto, resposta, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (session_id, s_id, s_nome, ref, texto, val, now))
                            
        con.commit()
        print(f'📊 Questionário Likert salvo para a sessão {session_id}')
    finally:
        con.close()


def get_likert_geral():
    """Retorna todos os dados do Likert para o Dashboard."""
    con = sqlite3.connect(DB_PATH)
    try:
        rows = con.execute('''
            SELECT sq.session_id, sq.nome_aluno, sq.tema, sq.data_hora,
                   rl.secao_nome, rl.pergunta_texto, rl.resposta, rl.timestamp
            FROM respostas_likert rl
            JOIN sessoes_quiz sq ON sq.session_id = rl.session_id
            ORDER BY sq.data_hora DESC, rl.timestamp ASC
        ''').fetchall()
        
        sessoes = {}
        for r in rows:
            sid, aluno, tema, dt, secao, perg, resp, ts = r
            if sid not in sessoes:
                sessoes[sid] = {
                    'session_id': sid, 'nome_aluno': aluno, 'tema': tema, 'data_hora': dt,
                    'respostas': []
                }
            sessoes[sid]['respostas'].append({
                'secao': secao, 'pergunta': perg, 'resposta': resp, 'timestamp': ts
            })
            
        return list(sessoes.values())
    finally:
        con.close()
