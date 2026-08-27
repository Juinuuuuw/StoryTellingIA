import React, { useRef } from 'react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { Download, CheckCircle2 } from 'lucide-react';

interface PosterPreviewProps {
  campaign: string;
  title: string;
  story: string;
  studentName: string;
  schoolName: string;
  isGenerating: boolean;
}

export function PosterPreview({
  campaign,
  title,
  story,
  studentName,
  schoolName,
  isGenerating
}: PosterPreviewProps) {
  const posterRef = useRef<HTMLDivElement>(null);

  const handleDownload = async () => {
    if (!posterRef.current) return;
    
    try {
      const canvas = await html2canvas(posterRef.current, { scale: 2 });
      const imgData = canvas.toDataURL('image/png');
      
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'px',
        format: [canvas.width, canvas.height]
      });
      
      pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height);
      pdf.save(`cartaz_${studentName.replace(' ', '_')}.pdf`);
    } catch (err) {
      console.error('Failed to generate PDF', err);
    }
  };

  return (
    <div className="poster-container">
      <div className="poster" ref={posterRef}>
        {isGenerating && (
          <div className="generating-overlay">
            <div className="spinner"></div>
            <p>A IA está criando sua obra...</p>
          </div>
        )}
        
        <div className="poster-header">
          <span className="badge">Campanha da Semana</span>
          <h2 className="poster-campaign">{campaign}</h2>
        </div>
        
        <img 
          src="/illustration.jpg" 
          alt="Illustration" 
          className="poster-image" 
        />
        
        <div className="poster-content">
          <h3 className="poster-title">"{title}"</h3>
          <p className="poster-story">{story}</p>
        </div>
        
        <div className="poster-footer">
          <div className="author-info">
            <span style={{ color: 'var(--text-muted)' }}>Autor(a):</span>
            <div style={{ fontSize: '1.1rem', color: 'var(--primary)' }}>👧 {studentName}</div>
          </div>
          <div className="school-info">
            🏫 {schoolName}
          </div>
        </div>
      </div>

      <button className="btn btn-secondary" onClick={handleDownload} disabled={isGenerating}>
        <Download size={18} />
        Baixar Cartaz em PDF
      </button>
      
      <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
        <CheckCircle2 size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '4px' }} />
        Validação pedagógica concluída
      </p>
    </div>
  );
}
