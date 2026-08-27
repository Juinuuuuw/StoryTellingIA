import React, { useState } from 'react';
import { Sparkles, Settings, User } from 'lucide-react';
import { PosterPreview } from './components/PosterPreview';

function App() {
  const [campaign, setCampaign] = useState('Combate ao Bullying');
  const [schoolName, setSchoolName] = useState('Escola Caminho do Saber');
  
  const [studentName, setStudentName] = useState('Maria Clara');
  const [studentInput, setStudentInput] = useState('Eu acho que a gente tem que chamar quem tá sozinho pra brincar com a gente, assim ninguém fica triste no recreio.');
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState({
    title: 'O poder de um convite',
    story: 'Maria Clara imaginou uma escola onde todos eram diferentes, mas ninguém era deixado de lado. Quando via alguém sozinho no banco do pátio, ela logo estendia a mão e dizia: "Vem brincar com a gente!". Afinal, a brincadeira sempre fica mais legal quando tem espaço para todo mundo.'
  });

  const handleGenerate = () => {
    setIsGenerating(true);
    // Simulating API calls to the 2 AIs
    setTimeout(() => {
      setResult({
        title: 'O poder de um convite',
        story: 'Maria Clara imaginou uma escola onde todos eram diferentes, mas ninguém era deixado de lado. Quando via alguém sozinho no banco do pátio, ela logo estendia a mão e dizia: "Vem brincar com a gente!". Afinal, a brincadeira sempre fica mais legal quando tem espaço para todo mundo.'
      });
      setIsGenerating(false);
    }, 2000);
  };

  return (
    <div className="app-container">
      {/* Left Panel: Configuration & Input */}
      <div className="panel">
        <div className="header">
          <h1>EduCanvas Framework 🚀</h1>
          <p>Configure a campanha e simule a interação da criança.</p>
        </div>

        <div style={{ padding: '1.5rem', background: '#F3F4F6', borderRadius: '8px' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem', fontSize: '1.1rem' }}>
            <Settings size={18} /> Configuração da Escola
          </h3>
          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label>Nome da Escola</label>
            <input 
              type="text" 
              className="form-control" 
              value={schoolName}
              onChange={(e) => setSchoolName(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Tema da Campanha (Semana)</label>
            <select 
              className="form-control"
              value={campaign}
              onChange={(e) => setCampaign(e.target.value)}
            >
              <option value="Combate ao Bullying">Combate ao Bullying</option>
              <option value="Semana do Meio Ambiente">Semana do Meio Ambiente</option>
              <option value="Incentivo à Leitura">Incentivo à Leitura</option>
              <option value="Saúde e Higiene">Saúde e Higiene</option>
            </select>
          </div>
        </div>

        <div style={{ padding: '1.5rem', border: '1px solid var(--border)', borderRadius: '8px' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem', fontSize: '1.1rem', color: 'var(--primary)' }}>
            <User size={18} /> Interação da Criança
          </h3>
          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label>Nome da Criança</label>
            <input 
              type="text" 
              className="form-control" 
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Ideia / Mensagem da Criança sobre "{campaign}"</label>
            <textarea 
              className="form-control" 
              value={studentInput}
              onChange={(e) => setStudentInput(e.target.value)}
              placeholder="O que você acha sobre esse assunto?"
            />
          </div>
        </div>

        <button 
          className="btn btn-primary" 
          onClick={handleGenerate}
          disabled={isGenerating}
          style={{ marginTop: 'auto' }}
        >
          <Sparkles size={18} />
          {isGenerating ? 'Processando IAs...' : 'Gerar Produção (IA Pedagógica + IA Criativa)'}
        </button>
      </div>

      {/* Right Panel: Result & Export */}
      <div className="panel" style={{ background: '#F8FAFC' }}>
        <div className="header" style={{ textAlign: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.25rem' }}>Produto Final</h2>
          <p>Pronto para validação e impressão</p>
        </div>
        
        <PosterPreview 
          campaign={campaign}
          title={result.title}
          story={result.story}
          studentName={studentName}
          schoolName={schoolName}
          isGenerating={isGenerating}
        />
      </div>
    </div>
  );
}

export default App;
