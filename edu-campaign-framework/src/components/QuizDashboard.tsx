import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  Download,
  Search,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RefreshCw,
  ArrowLeft,
  Trophy,
  BookOpen,
  Users,
  TrendingUp,
  Calendar,
  Filter,
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────

interface SessaoResumo {
  session_id: string;
  nome_aluno: string;
  tema: string;
  skill: string;
  data_hora: string;
  total_perguntas: number;
  acertos: number;
  percentual: number;
}

interface PerguntaDetalhe {
  id: number;
  ordem: number;
  pergunta: string;
  opcoes: string[];
  resposta_correta: number;
  ato: number;
  resposta_dada: number | null;
  deu_up: boolean;
  correta: boolean;
}

interface SessaoDetalhe extends SessaoResumo {
  perguntas: PerguntaDetalhe[];
}

interface ResultadoGeral {
  total_sessoes: number;
  total_perguntas_respondidas: number;
  total_acertos: number;
  percentual_geral: number;
  sessoes: SessaoResumo[];
}

// ─────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────

const API = 'http://localhost:5000';

const colorForPct = (pct: number) => {
  if (pct >= 80) return '#10B981'; // green
  if (pct >= 50) return '#F59E0B'; // amber
  return '#EF4444'; // red
};

const formatDate = (iso: string) => {
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso; }
};

const LETRAS = ['A', 'B', 'C', 'D'];

// ─────────────────────────────────────────────────────────────
// Mini bar chart (no external lib)
// ─────────────────────────────────────────────────────────────

function BarraDesempenho({ sessoes }: { sessoes: SessaoResumo[] }) {
  // Agrupa por tema
  const byTema: Record<string, { acertos: number; total: number }> = {};
  sessoes.forEach((s) => {
    if (!byTema[s.tema]) byTema[s.tema] = { acertos: 0, total: 0 };
    byTema[s.tema].acertos += s.acertos;
    byTema[s.tema].total += s.total_perguntas;
  });

  const temas = Object.entries(byTema).map(([tema, v]) => ({
    tema,
    pct: v.total > 0 ? Math.round((v.acertos / v.total) * 100) : 0,
    acertos: v.acertos,
    total: v.total,
  }));

  if (temas.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {temas.map((t) => (
        <div key={t.tema}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 500, maxWidth: '70%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {t.tema}
            </span>
            <span style={{ fontSize: '0.85rem', color: colorForPct(t.pct), fontWeight: 700 }}>
              {t.pct}% ({t.acertos}/{t.total})
            </span>
          </div>
          <div style={{ height: '10px', background: '#E5E7EB', borderRadius: '999px', overflow: 'hidden' }}>
            <div
              style={{
                height: '100%',
                width: `${t.pct}%`,
                background: colorForPct(t.pct),
                borderRadius: '999px',
                transition: 'width 0.6s ease',
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Session Detail Modal / Panel
// ─────────────────────────────────────────────────────────────

function DetalhesSessao({ sessao, onFechar }: { sessao: SessaoDetalhe; onFechar: () => void }) {
  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
      zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '1rem',
    }}
      onClick={onFechar}
    >
      <div
        style={{
          background: 'white', borderRadius: '16px', width: '100%', maxWidth: '780px',
          maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '1.5rem 2rem',
          background: 'linear-gradient(135deg, #4F46E5, #7C3AED)',
          color: 'white',
          borderRadius: '16px 16px 0 0',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h2 style={{ color: 'white', fontSize: '1.4rem', marginBottom: '0.25rem' }}>
                {sessao.nome_aluno}
              </h2>
              <p style={{ opacity: 0.85, fontSize: '0.9rem' }}>
                {sessao.tema} · {sessao.skill} · {formatDate(sessao.data_hora)}
              </p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '2rem', fontWeight: 700 }}>{sessao.percentual}%</div>
              <div style={{ opacity: 0.85, fontSize: '0.85rem' }}>{sessao.acertos}/{sessao.total_perguntas} acertos</div>
            </div>
          </div>
        </div>

        {/* Body */}
        <div style={{ padding: '1.5rem 2rem', overflowY: 'auto', flex: 1 }}>
          {sessao.perguntas.length === 0 ? (
            <p style={{ color: '#6B7280', textAlign: 'center', padding: '2rem 0' }}>
              Nenhuma pergunta registrada para esta sessão.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {sessao.perguntas.map((p, i) => {
                const icon = p.deu_up
                  ? <HelpCircle size={18} color="#F59E0B" />
                  : p.correta
                  ? <CheckCircle2 size={18} color="#10B981" />
                  : <XCircle size={18} color="#EF4444" />;

                return (
                  <div key={p.id} style={{
                    border: '1px solid #E5E7EB', borderRadius: '12px',
                    padding: '1rem 1.25rem',
                    background: p.correta ? '#F0FDF4' : p.deu_up ? '#FFFBEB' : '#FEF2F2',
                  }}>
                    <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.75rem' }}>
                      {icon}
                      <strong style={{ fontSize: '0.9rem', flex: 1 }}>
                        {i + 1}. {p.pergunta}
                      </strong>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
                      {p.opcoes.map((opc, idx) => {
                        const isCorreta = idx === p.resposta_correta;
                        const isAluno = idx === p.resposta_dada;
                        let bg = '#F3F4F6';
                        let border = '1px solid #E5E7EB';
                        let fw: 'normal' | 'bold' = 'normal';
                        if (isCorreta) { bg = '#D1FAE5'; border = '1px solid #6EE7B7'; fw = 'bold'; }
                        if (isAluno && !isCorreta) { bg = '#FEE2E2'; border = '1px solid #FCA5A5'; }
                        return (
                          <div key={idx} style={{
                            padding: '0.4rem 0.75rem', borderRadius: '8px',
                            background: bg, border, fontSize: '0.82rem', fontWeight: fw,
                            display: 'flex', alignItems: 'center', gap: '6px',
                          }}>
                            <span style={{
                              width: '20px', height: '20px', borderRadius: '50%',
                              background: isCorreta ? '#10B981' : (isAluno ? '#EF4444' : '#9CA3AF'),
                              color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
                              fontSize: '0.7rem', fontWeight: 'bold', flexShrink: 0,
                            }}>
                              {LETRAS[idx]}
                            </span>
                            {opc}
                            {isCorreta && !isAluno && <span style={{ marginLeft: 'auto', fontSize: '0.7rem', color: '#10B981' }}>✓ correta</span>}
                            {isAluno && !isCorreta && <span style={{ marginLeft: 'auto', fontSize: '0.7rem', color: '#EF4444' }}>✗ escolhida</span>}
                            {isAluno && isCorreta && <span style={{ marginLeft: 'auto', fontSize: '0.7rem', color: '#10B981' }}>✓ acertou</span>}
                          </div>
                        );
                      })}
                    </div>
                    {p.deu_up && (
                      <p style={{ fontSize: '0.8rem', color: '#92400E', marginTop: '0.5rem' }}>
                        ⚠ Aluno selecionou "Não me lembro"
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '1rem 2rem', borderTop: '1px solid #E5E7EB', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-primary" onClick={onFechar} style={{ fontSize: '0.9rem' }}>
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Main Dashboard Component
// ─────────────────────────────────────────────────────────────

interface QuizDashboardProps {
  onVoltar: () => void;
}

export function QuizDashboard({ onVoltar }: QuizDashboardProps) {
  const [dados, setDados] = useState<ResultadoGeral | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [sessaoDetalhe, setSessaoDetalhe] = useState<SessaoDetalhe | null>(null);
  const [loadingDetalhe, setLoadingDetalhe] = useState(false);
  const [exportando, setExportando] = useState(false);

  // Filtros
  const [filtroAluno, setFiltroAluno] = useState('');
  const [filtroTema, setFiltroTema] = useState('');
  const [filtroDataDe, setFiltroDataDe] = useState('');
  const [filtroDataAte, setFiltroDataAte] = useState('');
  const [mostrarFiltros, setMostrarFiltros] = useState(false);

  // Sort
  const [sortKey, setSortKey] = useState<keyof SessaoResumo>('data_hora');
  const [sortAsc, setSortAsc] = useState(false);

  const carregarDados = useCallback(async () => {
    setLoading(true);
    setErro(null);
    try {
      const res = await fetch(`${API}/resultados`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: ResultadoGeral = await res.json();
      setDados(json);
    } catch (e: unknown) {
      setErro(`Não foi possível conectar ao servidor. Verifique se ele está rodando em ${API}.`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { carregarDados(); }, [carregarDados]);

  const abrirDetalhe = async (sid: string) => {
    setLoadingDetalhe(true);
    try {
      const res = await fetch(`${API}/resultados?session_id=${sid}`);
      const json: SessaoDetalhe = await res.json();
      setSessaoDetalhe(json);
    } catch {
      alert('Erro ao carregar detalhes da sessão.');
    } finally {
      setLoadingDetalhe(false);
    }
  };

  const exportarExcel = async () => {
    setExportando(true);
    try {
      const res = await fetch(`${API}/exportar_excel`);
      if (!res.ok) {
        const err = await res.json();
        alert(`Erro ao exportar: ${err.msg}`);
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `quiz_resultados_${new Date().toISOString().slice(0,10)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      alert('Erro ao baixar o Excel. Verifique se o openpyxl está instalado no servidor.');
    } finally {
      setExportando(false);
    }
  };

  const handleSort = (key: keyof SessaoResumo) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(true); }
  };

  // Filtragem
  const sessoesFiltradas = (dados?.sessoes ?? [])
    .filter((s) => {
      if (filtroAluno && !s.nome_aluno.toLowerCase().includes(filtroAluno.toLowerCase())) return false;
      if (filtroTema && s.tema !== filtroTema) return false;
      if (filtroDataDe && s.data_hora < filtroDataDe) return false;
      if (filtroDataAte && s.data_hora > filtroDataAte + 'T23:59:59') return false;
      return true;
    })
    .sort((a, b) => {
      const va = a[sortKey] as string | number;
      const vb = b[sortKey] as string | number;
      const cmp = va < vb ? -1 : va > vb ? 1 : 0;
      return sortAsc ? cmp : -cmp;
    });

  const temas = Array.from(new Set((dados?.sessoes ?? []).map((s) => s.tema)));

  // ── Header stats ──
  const statCard = (icon: React.ReactNode, label: string, value: string | number, cor?: string) => (
    <div style={{
      background: 'white', borderRadius: '12px', padding: '1.25rem 1.5rem',
      border: '1px solid #E5E7EB', display: 'flex', alignItems: 'center', gap: '1rem',
      boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
    }}>
      <div style={{
        width: '44px', height: '44px', borderRadius: '10px',
        background: '#EEF2FF', display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: cor ?? '#4F46E5', flexShrink: 0,
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: cor ?? '#111827', lineHeight: 1 }}>{value}</div>
        <div style={{ fontSize: '0.8rem', color: '#6B7280', marginTop: '2px' }}>{label}</div>
      </div>
    </div>
  );

  const SortIcon = ({ col }: { col: keyof SessaoResumo }) =>
    sortKey === col
      ? (sortAsc ? <ChevronUp size={14} /> : <ChevronDown size={14} />)
      : null;

  const thStyle: React.CSSProperties = {
    padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.8rem',
    fontWeight: 600, color: '#4F46E5', background: '#EEF2FF',
    cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap',
  };
  const tdStyle: React.CSSProperties = { padding: '0.75rem 1rem', fontSize: '0.875rem', color: '#374151' };

  return (
    <div style={{
      minHeight: '100vh', background: '#F3F4F6', padding: '2rem',
      fontFamily: 'Inter, sans-serif',
    }}>
      {/* ── Page Header ── */}
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button
              onClick={onVoltar}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6B7280', display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 style={{ fontSize: '1.75rem', color: '#4F46E5', margin: 0, fontFamily: 'Fredoka, sans-serif' }}>
                📊 Dashboard do Quiz
              </h1>
              <p style={{ color: '#6B7280', fontSize: '0.875rem', marginTop: '2px' }}>
                Resultados e desempenho por sessão
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button className="btn" style={{ background: '#E5E7EB', color: '#374151', fontSize: '0.875rem', padding: '0.6rem 1rem' }} onClick={carregarDados}>
              <RefreshCw size={16} />
              Atualizar
            </button>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.875rem', padding: '0.6rem 1rem' }}
              onClick={exportarExcel}
              disabled={exportando || !dados}
            >
              <Download size={16} />
              {exportando ? 'Exportando...' : 'Exportar Excel'}
            </button>
          </div>
        </div>

        {/* ── Loading / Error ── */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '4rem', color: '#6B7280' }}>
            <div className="spinner" style={{ margin: '0 auto 1rem' }} />
            <p>Carregando resultados...</p>
          </div>
        )}

        {erro && !loading && (
          <div style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '12px', padding: '1.5rem', color: '#991B1B', marginBottom: '1.5rem' }}>
            <strong>⚠ Erro:</strong> {erro}
          </div>
        )}

        {!loading && dados && (
          <>
            {/* ── Stats ── */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
              {statCard(<Users size={22} />, 'Sessões realizadas', dados.total_sessoes)}
              {statCard(<BookOpen size={22} />, 'Perguntas respondidas', dados.total_perguntas_respondidas)}
              {statCard(<Trophy size={22} />, 'Total de acertos', dados.total_acertos, '#10B981')}
              {statCard(<TrendingUp size={22} />, 'Aproveitamento geral',
                `${dados.percentual_geral}%`,
                colorForPct(dados.percentual_geral)
              )}
            </div>

            {/* ── Gráfico por Tema + Filtros ── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
              <div style={{ background: 'white', borderRadius: '12px', padding: '1.5rem', border: '1px solid #E5E7EB' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BarChart3 size={18} color="#4F46E5" /> Desempenho por Tema
                </h3>
                <BarraDesempenho sessoes={sessoesFiltradas} />
                {sessoesFiltradas.length === 0 && <p style={{ color: '#9CA3AF', fontSize: '0.875rem' }}>Nenhuma sessão encontrada.</p>}
              </div>

              <div style={{ background: 'white', borderRadius: '12px', padding: '1.5rem', border: '1px solid #E5E7EB' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                  <h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                    <Filter size={18} color="#4F46E5" /> Filtros
                  </h3>
                  <button
                    onClick={() => setMostrarFiltros(!mostrarFiltros)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#4F46E5', fontSize: '0.8rem' }}
                  >
                    {mostrarFiltros ? 'Ocultar' : 'Mostrar'}
                  </button>
                </div>

                {mostrarFiltros && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <div style={{ position: 'relative' }}>
                      <Search size={15} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#9CA3AF' }} />
                      <input
                        className="form-control"
                        placeholder="Filtrar por aluno..."
                        value={filtroAluno}
                        onChange={(e) => setFiltroAluno(e.target.value)}
                        style={{ paddingLeft: '32px', fontSize: '0.875rem', padding: '0.6rem 0.75rem 0.6rem 32px' }}
                      />
                    </div>
                    <select
                      className="form-control"
                      value={filtroTema}
                      onChange={(e) => setFiltroTema(e.target.value)}
                      style={{ fontSize: '0.875rem', padding: '0.6rem 0.75rem' }}
                    >
                      <option value="">Todos os temas</option>
                      {temas.map((t) => <option key={t} value={t}>{t}</option>)}
                    </select>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <Calendar size={15} color="#9CA3AF" style={{ flexShrink: 0 }} />
                      <input type="date" className="form-control" value={filtroDataDe} onChange={(e) => setFiltroDataDe(e.target.value)} style={{ fontSize: '0.875rem', padding: '0.5rem' }} />
                      <span style={{ color: '#9CA3AF', flexShrink: 0 }}>até</span>
                      <input type="date" className="form-control" value={filtroDataAte} onChange={(e) => setFiltroDataAte(e.target.value)} style={{ fontSize: '0.875rem', padding: '0.5rem' }} />
                    </div>
                    <button
                      onClick={() => { setFiltroAluno(''); setFiltroTema(''); setFiltroDataDe(''); setFiltroDataAte(''); }}
                      style={{ background: 'none', border: 'none', color: '#6B7280', cursor: 'pointer', fontSize: '0.8rem', textAlign: 'left' }}
                    >
                      Limpar filtros
                    </button>
                  </div>
                )}

                {!mostrarFiltros && (
                  <div style={{ color: '#9CA3AF', fontSize: '0.875rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    <p>{sessoesFiltradas.length} sessão(ões) exibida(s)</p>
                    {(filtroAluno || filtroTema || filtroDataDe || filtroDataAte) && (
                      <p style={{ color: '#4F46E5', fontSize: '0.8rem' }}>⚙ Filtros ativos</p>
                    )}
                    <button
                      onClick={() => setMostrarFiltros(true)}
                      className="btn"
                      style={{ background: '#EEF2FF', color: '#4F46E5', fontSize: '0.8rem', padding: '0.5rem 0.75rem', marginTop: '0.5rem' }}
                    >
                      <Filter size={14} /> Abrir filtros
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* ── Table ── */}
            <div style={{ background: 'white', borderRadius: '12px', border: '1px solid #E5E7EB', overflow: 'hidden' }}>
              <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #E5E7EB', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ fontSize: '1rem', margin: 0 }}>
                  Sessões ({sessoesFiltradas.length})
                </h3>
                <span style={{ fontSize: '0.8rem', color: '#9CA3AF' }}>
                  Clique em uma sessão para ver detalhes
                </span>
              </div>

              {sessoesFiltradas.length === 0 ? (
                <div style={{ padding: '3rem', textAlign: 'center', color: '#9CA3AF' }}>
                  Nenhuma sessão encontrada com os filtros aplicados.
                </div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr>
                        {([
                          ['nome_aluno', 'Aluno'],
                          ['tema', 'Tema'],
                          ['skill', 'Skill'],
                          ['data_hora', 'Data/Hora'],
                          ['total_perguntas', 'Perguntas'],
                          ['acertos', 'Acertos'],
                          ['percentual', 'Aproveit.'],
                        ] as [keyof SessaoResumo, string][]).map(([key, label]) => (
                          <th key={key} style={thStyle} onClick={() => handleSort(key)}>
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                              {label} <SortIcon col={key} />
                            </span>
                          </th>
                        ))}
                        <th style={{ ...thStyle, cursor: 'default' }}>Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sessoesFiltradas.map((s, i) => (
                        <tr
                          key={s.session_id}
                          style={{ borderTop: '1px solid #F3F4F6', background: i % 2 === 0 ? 'white' : '#FAFAFA', cursor: 'pointer' }}
                          onClick={() => abrirDetalhe(s.session_id)}
                        >
                          <td style={tdStyle}><strong>{s.nome_aluno}</strong></td>
                          <td style={tdStyle}>
                            <span style={{
                              background: '#EEF2FF', color: '#4F46E5', borderRadius: '999px',
                              padding: '2px 8px', fontSize: '0.75rem', fontWeight: 600,
                            }}>{s.tema}</span>
                          </td>
                          <td style={tdStyle}>{s.skill}</td>
                          <td style={tdStyle}>{formatDate(s.data_hora)}</td>
                          <td style={{ ...tdStyle, textAlign: 'center' }}>{s.total_perguntas}</td>
                          <td style={{ ...tdStyle, textAlign: 'center' }}>{s.acertos}</td>
                          <td style={{ ...tdStyle, textAlign: 'center' }}>
                            <span style={{
                              color: colorForPct(s.percentual), fontWeight: 700, fontSize: '0.95rem',
                            }}>
                              {s.percentual}%
                            </span>
                          </td>
                          <td style={{ ...tdStyle, textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                            <button
                              className="btn"
                              style={{ background: '#EEF2FF', color: '#4F46E5', fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                              onClick={() => abrirDetalhe(s.session_id)}
                              disabled={loadingDetalhe}
                            >
                              Ver detalhes
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* ── Detalhe Modal ── */}
      {sessaoDetalhe && (
        <DetalhesSessao sessao={sessaoDetalhe} onFechar={() => setSessaoDetalhe(null)} />
      )}
    </div>
  );
}
