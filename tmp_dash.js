
Chart.defaults.color = 'rgba(255, 255, 255, 0.6)';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
Chart.defaults.font.family = "'Montserrat', sans-serif";
const API=(window.location.protocol==='file:')?'http://127.0.0.1:5000':window.location.origin, POLL=5000, LETRAS=['A','B','C','D'];
let dQ={}, dH=[], cH={}, cQ={};
let qSK='data_hora',qSA=false,hSK='data_inicio',hSA=false;
let qExp=null,hExp=null;
let chT=null,chP=null;

const pct=p=>p>=80?'#10B981':p>=50?'#F59E0B':'#EF4444';
const fmt=iso=>{try{return new Date(iso).toLocaleString('pt-BR',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'})}catch{return iso}};
const bpct=p=>{const c=p>=80?'badge-green':p>=50?'badge-amber':'badge-red';return`<span class="badge ${c}">${p}%</span>`};
const SMAP={aguardando:{l:'Aguardando',b:'#F3F4F6',c:'#64748B'},pensando:{l:'Pensando...',b:'#EEF2FF',c:'#4F46E5'},ativo:{l:'Historia ativa',b:'#ECFDF5',c:'#059669'},modal:{l:'Escolhendo',b:'#FFF7ED',c:'#D97706'},quiz_gerando:{l:'Gerando quiz',b:'#FFF7ED',c:'#D97706'},quiz:{l:'Quiz em andamento',b:'#EEF2FF',c:'#4F46E5'},quiz_fim:{l:'Quiz encerrado',b:'#ECFDF5',c:'#059669'}};

function trocarAba(btn,id){document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.getElementById('sec-'+id).classList.add('active');btn.classList.add('active')}

async function fQ(){try{const r=await fetch(API+'/resultados');if(!r.ok)throw 0;dQ=await r.json();uiQ()}catch{document.getElementById('lu-top').textContent='Servidor nao responde'}}
async function fH(){try{const r=await fetch(API+'/historia_sessao');if(!r.ok)return;dH=await r.json();uiH()}catch{}}
async function fL(){try{const r=await fetch(API+'/status_visualizador');if(!r.ok)return;renderLive(await r.json())}catch{}}

function uiQ(){
  if(!dQ)return;
  const t=new Date().toLocaleTimeString('pt-BR');
  document.getElementById('lu-top').textContent='Atualizado: '+t;
  document.getElementById('q-lu').textContent=t;
  document.getElementById('s-s').textContent=dQ.total_sessoes||0;
  document.getElementById('s-p').textContent=dQ.total_perguntas_respondidas||0;
  document.getElementById('s-a').textContent=dQ.total_acertos||0;
  const p=dQ.percentual_geral||0;
  document.getElementById('s-pct').textContent=p+'%';
  document.getElementById('s-pct').style.color=pct(p);
  document.getElementById('s-bar').style.width=p+'%';
  document.getElementById('s-bar').style.background=pct(p);
  const temas=[...new Set((dQ.sessoes||[]).map(s=>s.tema))];
  const sel=document.getElementById('q-ft'),val=sel.value;
  sel.innerHTML='<option value="">Todos os temas</option>'+temas.map(t=>`<option${t===val?' selected':''}>${t}</option>`).join('');
  renderQCharts();renderQT();
  document.getElementById('loading-overlay').style.display='none';
}

function getQF(){
  const al=document.getElementById('q-fa').value.toLowerCase(),te=document.getElementById('q-ft').value,de=document.getElementById('q-fd').value,ate=document.getElementById('q-fa2').value;
  return(dQ?.sessoes||[]).filter(s=>{
    if(al&&!s.nome_aluno.toLowerCase().includes(al))return false;
    if(te&&s.tema!==te)return false;
    if(de&&s.data_hora<de)return false;
    if(ate&&s.data_hora>ate+'T23:59:59')return false;
    return true;
  }).sort((a,b)=>{const c=a[qSK]<b[qSK]?-1:a[qSK]>b[qSK]?1:0;return qSA?c:-c});
}

function renderQCharts(){
  const s=getQF(),bT={};
  s.forEach(x=>{if(!bT[x.tema])bT[x.tema]={a:0,t:0};bT[x.tema].a+=x.acertos;bT[x.tema].t+=x.total_perguntas});
  const tms=Object.keys(bT),ps=tms.map(t=>bT[t].t>0?Math.round(bT[t].a/bT[t].t*100):0);
  const ctxT=document.getElementById('ct').getContext('2d');
  if(chT)chT.destroy();
  chT=new Chart(ctxT,{type:'bar',data:{labels:tms.length?tms:['(sem dados)'],datasets:[{label:'% Acertos',data:tms.length?ps:[0],backgroundColor:ps.map(pct),borderRadius:8}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{min:0,max:100,ticks:{callback:v=>v+'%'},grid:{color:'rgba(255,255,255,0.1)'}},x:{grid:{display:false}}}}});
  const tA=s.reduce((a,x)=>a+x.acertos,0),tT=s.reduce((a,x)=>a+x.total_perguntas,0);
  const ctxP=document.getElementById('cp').getContext('2d');
  if(chP)chP.destroy();
  chP=new Chart(ctxP,{type:'doughnut',data:{labels:['Acertos','Erros/Desist.'],datasets:[{data:[tA,tT-tA],backgroundColor:['#10B981','#EF4444'],borderWidth:0,hoverOffset:6}]},options:{responsive:true,maintainAspectRatio:false,cutout:'65%',plugins:{legend:{position:'bottom',labels:{padding:14,font:{size:12}}}}}});
}

function renderQT(){
  renderQCharts();
  const ss=getQF(),tb=document.getElementById('q-tb');
  document.getElementById('q-tt').textContent='Sessoes de Quiz ('+ss.length+')';
  document.getElementById('q-cnt').textContent=ss.length+' sessao(oes)';
  document.getElementById('q-emp').style.display=ss.length?'none':'block';
  tb.innerHTML=ss.map(s=>{
    const ex=qExp===s.session_id;
    return`<tr onclick="qTog('${s.session_id}')"><td><strong>${s.nome_aluno}</strong></td><td><span class="badge badge-blue">${s.tema}</span></td><td style="color:var(--muted)">${s.skill}</td><td style="color:var(--muted);font-size:.82rem">${fmt(s.data_hora)}</td><td style="text-align:center">${s.total_perguntas}</td><td style="text-align:center;font-weight:600;color:var(--green)">${s.acertos}</td><td style="text-align:center">${bpct(s.percentual)}</td></tr>${ex?`<tr class="detail-row"><td colspan="7"><div class="detail-panel" id="qd-${s.session_id}"><em>Carregando...</em></div></td></tr>`:''}`;
  }).join('');
  if(qExp){const el=document.getElementById('qd-'+qExp);if(el){if(cQ[qExp])rQD(qExp);else fQD(qExp)}}
}
function qSort(k){qSK===k?qSA=!qSA:(qSK=k,qSA=true);renderQT()}
async function qTog(sid){qExp=qExp===sid?null:sid;renderQT();if(qExp&&!cQ[sid])await fQD(sid);else if(qExp)rQD(sid)}
async function fQD(sid){try{const r=await fetch(API+'/resultados?session_id='+sid);cQ[sid]=await r.json();rQD(sid)}catch{const el=document.getElementById('qd-'+sid);if(el)el.innerHTML='<p style="color:red">Erro.</p>'}}
function rQD(sid){
  const el=document.getElementById('qd-'+sid);if(!el)return;
  const d=cQ[sid];if(!d)return;
  const ps=d.perguntas||[];
  el.innerHTML=`<div style="display:flex;align-items:center;gap:1rem;margin-bottom:.75rem;flex-wrap:wrap"><strong>${d.nome_aluno}</strong><span class="badge badge-blue">${d.tema}</span><span style="color:var(--muted);font-size:.8rem">${fmt(d.data_hora)}</span><span style="margin-left:auto;font-weight:700;font-size:1.1rem;color:${pct(d.percentual)}">${d.percentual}% - ${d.acertos}/${d.total_perguntas}</span></div>${ps.length===0?'<p style="color:var(--muted)">Nenhuma pergunta registrada ainda.</p>':'<div class="questions-grid">'+ps.map((p,i)=>{const cl=p.deu_up?'up':p.correta?'correta':'errada',ic=p.deu_up?'<i data-lucide="help-circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>':p.correta?'<i data-lucide="check-circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>':'<i data-lucide="x-circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>';return`<div class="q-card ${cl}"><div class="q-num">Pergunta ${i+1} ${ic}</div><div class="q-text">${p.pergunta}</div><div class="opcoes-grid">${(p.opcoes||[]).map((o,idx)=>{const iC=idx===p.resposta_correta,iA=idx===p.resposta_dada,oc=iC?'correta':(iA&&!iC?'errada':''),bg=iC?'#10B981':iA?'#EF4444':'#9CA3AF';return`<div class="opcao ${oc}"><span class="letra" style="background:${bg}">${LETRAS[idx]}</span><span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${o}">${o}</span>${iC&&iA?'<span style="font-size:.65rem;color:#059669;flex-shrink:0">&#10003;</span>':''}${iC&&!iA?'<span style="font-size:.65rem;color:#059669;flex-shrink:0">certa</span>':''}${iA&&!iC?'<span style="font-size:.65rem;color:#DC2626;flex-shrink:0">&#10007;</span>':''}</div>`}).join('')}</div>${p.deu_up?'<p style="font-size:.72rem;color:#92400E;margin-top:.5rem"><i data-lucide="alert-triangle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i> Nao me lembro</p>':''}</div>`}).join('')+'</div>'}`;
}
function limparQ(){['q-fa','q-ft','q-fd','q-fa2'].forEach(id=>{const e=document.getElementById(id);e.tagName==='SELECT'?e.value='':e.value=''});renderQT()}


let dL=[];
let lExp=null;
let cL={};

async function fL_pesquisa(){
  try{
    const r=await fetch(API+'/likert_resultados');
    if(!r.ok)return;
    dL=await r.json();
    uiL();
  }catch(e){}
}

function uiL(){
  const t=new Date().toLocaleTimeString('pt-BR');
  document.getElementById('l-lu').textContent=t;
  renderLT();
}

function renderLT(){
  const fa=document.getElementById('l-fa').value.toLowerCase();
  const res = dL.filter(x => !fa || x.nome_aluno.toLowerCase().includes(fa) || (x.pre_id && x.pre_id.toLowerCase().includes(fa)));
  document.getElementById('l-tt').textContent='Pesquisas ('+res.length+')';
  document.getElementById('l-cnt').textContent=res.length+' pesquisa(s)';
  document.getElementById('l-emp').style.display=res.length?'none':'block';
  
  const tb = document.getElementById('l-tb');
  tb.innerHTML = res.map(s => {
    const ex = lExp === s.session_id;
    return `<tr onclick="lTog('${s.session_id}')">
      <td><strong><span style="color:var(--accent);">${s.pre_id || 'N/A'}</span></strong></td>
      <td><strong>${s.nome_aluno}</strong></td>
      <td><span class="badge badge-blue">${s.tema}</span></td>
      <td style="color:var(--muted);font-size:.82rem">${fmt(s.data_hora)}</td>
    </tr>${ex ? `<tr class="detail-row"><td colspan="4"><div class="detail-panel" id="ld-${s.session_id}"></div></td></tr>` : ''}`;
  }).join('');
  
  if(lExp) rLD(lExp);
}

function lTog(sid){
  lExp = lExp === sid ? null : sid;
  renderLT();
}

function rLD(sid){
  const el=document.getElementById('ld-'+sid);
  if(!el)return;
  const d = dL.find(x => x.session_id === sid);
  if(!d)return;
  
  let html = `<div style="display:flex;align-items:center;gap:1rem;margin-bottom:.75rem;flex-wrap:wrap"><strong>${d.nome_aluno}</strong><span style="color:var(--muted);font-size:.8rem">${fmt(d.data_hora)}</span></div>`;
  
  const agrupado = {};
  d.respostas.forEach(r => {
    if(!agrupado[r.secao]) agrupado[r.secao] = [];
    agrupado[r.secao].push(r);
  });
  
  Object.keys(agrupado).forEach(sec => {
    html += `<div style="margin-top:1rem;background:white;padding:1rem;border-radius:8px;border:1px solid #E2E8F0;">
      <h4 style="margin-bottom:10px;color:var(--primary);font-size:.9rem">${sec}</h4>
      <table style="width:100%;font-size:.8rem;"><tbody>`;
    agrupado[sec].forEach(p => {
      let cor = p.resposta >= 4 ? '#10B981' : (p.resposta <= 2 ? '#EF4444' : '#F59E0B');
      html += `<tr><td style="padding:4px 0">${p.pergunta}</td><td style="width:40px;text-align:right"><strong style="color:${cor}">${p.resposta}</strong></td></tr>`;
    });
    html += `</tbody></table></div>`;
  });
  
  el.innerHTML = html;
}

// HISTORIA
function uiH(){
  const t=new Date().toLocaleTimeString('pt-BR');
  document.getElementById('h-lu').textContent=t;
  const tot=dH.length,con=dH.filter(h=>h.status==='concluida').length,em=dH.filter(h=>h.status==='em_andamento').length,cen=dH.reduce((a,h)=>a+(h.total_cenas||0),0);
  document.getElementById('h-tot').textContent=tot;
  document.getElementById('h-con').textContent=con;
  document.getElementById('h-and').textContent=em;
  document.getElementById('h-cen').textContent=cen;
  const skills=[...new Set(dH.map(h=>h.skill).filter(Boolean))];
  const sel=document.getElementById('h-fs'),val=sel.value;
  sel.innerHTML='<option value="">Todos os skills</option>'+skills.map(s=>`<option${s===val?' selected':''}>${s}</option>`).join('');
  renderHT();
}
function getHF(){
  const al=document.getElementById('h-fa').value.toLowerCase(),sk=document.getElementById('h-fs').value,st=document.getElementById('h-fst').value;
  return(dH||[]).filter(h=>{
    if(al&&!h.nome_aluno.toLowerCase().includes(al))return false;
    if(sk&&h.skill!==sk)return false;
    if(st&&h.status!==st)return false;
    return true;
  }).sort((a,b)=>{const c=a[hSK]<b[hSK]?-1:a[hSK]>b[hSK]?1:0;return hSA?c:-c});
}
function renderHT(){
  const hs=getHF(),tb=document.getElementById('h-tb');
  document.getElementById('h-tt').textContent='Historias ('+hs.length+')';
  document.getElementById('h-cnt').textContent=hs.length+' historia(s)';
  document.getElementById('h-emp').style.display=hs.length?'none':'block';
  tb.innerHTML=hs.map(h=>{
    const ex=hExp===h.session_id;
    const sb=h.status==='concluida'?'<span class="badge badge-green">Concluida</span>':'<span class="badge badge-amber">Em andamento</span>';
    return`<tr onclick="hTog('${h.session_id}')"><td><strong>${h.nome_aluno}</strong></td><td style="color:var(--muted)">${h.skill}</td><td><span class="badge badge-blue">${h.tema||'-'}</span></td><td style="color:var(--muted);font-size:.82rem">${fmt(h.data_inicio)}</td><td style="text-align:center">${h.total_cenas||0}</td><td style="text-align:center">${sb}</td></tr>${ex?`<tr class="detail-row"><td colspan="6"><div class="detail-panel" id="hd-${h.session_id}"><em>Carregando...</em></div></td></tr>`:''}`;
  }).join('');
  if(hExp){const el=document.getElementById('hd-'+hExp);if(el){if(cH[hExp])rHD(hExp);else fHD(hExp)}}
}
function hSort(k){hSK===k?hSA=!hSA:(hSK=k,hSA=true);renderHT()}
async function hTog(sid){hExp=hExp===sid?null:sid;renderHT();if(hExp&&!cH[sid])await fHD(sid);else if(hExp)rHD(sid)}
async function fHD(sid){try{const r=await fetch(API+'/historia_sessao?session_id='+sid);const d=await r.json();if(d.status==='erro')throw new Error(d.msg);cH[sid]=d;rHD(sid)}catch(e){const el=document.getElementById('hd-'+sid);if(el)el.innerHTML=`<p style="color:var(--amber)">Dados nao disponiveis. Reinicie o servidor para ativar o registro de historias.</p>`}}
function rHD(sid){
  const el=document.getElementById('hd-'+sid);if(!el)return;
  const d=cH[sid];if(!d)return;
  const cs=d.cenas||[];
  el.innerHTML=`<div style="display:flex;align-items:center;gap:1rem;margin-bottom:.75rem;flex-wrap:wrap"><strong>${d.nome_aluno}</strong><span class="badge badge-blue">${d.skill}</span><span style="color:var(--muted);font-size:.8rem">${fmt(d.data_inicio)}</span>${d.data_fim?`<span style="color:var(--muted);font-size:.8rem"><i data-lucide="arrow-right" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i> ${fmt(d.data_fim)}</span>`:''}<span style="margin-left:auto;font-size:.85rem;color:var(--muted)">${cs.length} cena(s)</span></div>${cs.length===0?'<p style="color:var(--muted)">Nenhuma cena registrada ainda.</p>':'<div class="cena-timeline">'+cs.map((c,i)=>{const ac='ato'+(c.ato||1),ae=c.ato===3?'<i data-lucide="theater" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>':c.ato===2?'<i data-lucide="zap" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>':'<i data-lucide="sunrise" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>';const ops=Array.isArray(c.opcoes)?c.opcoes:[];const tr=c.narrativa&&c.narrativa.length>200;return`<div class="cena-item"><div class="cena-dot ${ac}">${ae}</div><div class="cena-body"><div class="cena-header"><span class="badge badge-purple">Ato ${c.ato||1}</span><span class="badge" style="background:#F1F5F9;color:#64748B">${c.step_id}</span>${c.npc_principal?`<span style="font-size:.75rem;color:var(--muted)">com ${c.npc_principal}</span>`:''}<span style="margin-left:auto;font-size:.72rem;color:var(--muted)">${fmt(c.timestamp_cena)}</span></div><div class="cena-narrativa" id="nr-${c.id}">${c.narrativa||'-'}</div>${tr?`<button class="cena-toggle" onclick="togN('${c.id}')">&#9660; ver mais</button>`:''}<div style="margin-top:.6rem;flex-wrap:wrap">${ops.map(o=>`<span class="opcao-hist${c.escolha_feita===o?' escolhida':''}">${o}</span>`).join('')}</div>${c.escolha_feita?`<div style="font-size:.72rem;color:var(--primary);font-weight:600;margin-top:.4rem"><i data-lucide="arrow-right" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i> Aluno escolheu: "${c.escolha_feita}"</div>`:ops.length>0?'<div style="font-size:.72rem;color:var(--amber);margin-top:.4rem"><i data-lucide="hourglass" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i> Aguardando escolha...</div>':''}</div></div>`;}).join('')+'</div>'}`;
}
function togN(id){const el=document.getElementById('nr-'+id),btn=el.nextElementSibling;if(el.classList.contains('expanded')){el.classList.remove('expanded');btn.innerHTML='&#9660; ver mais'}else{el.classList.add('expanded');btn.innerHTML='&#9650; ver menos'}}
function limparH(){['h-fa','h-fs','h-fst'].forEach(id=>{document.getElementById(id).value=''});renderHT()}

// LIVE
function renderLive(d){
  const m=SMAP[d.status]||{l:d.status,b:'#F3F4F6',c:'#64748B'};
  const bg=document.getElementById('lv-badge');bg.textContent=m.l;bg.style.background=m.b;bg.style.color=m.c;
  document.getElementById('lv-st').textContent=m.l;
  const sid=d.session_id;
  // Show pre_id if available
  const preEntry=(dP||[]).find(p=>p.session_id===sid);
  if(preEntry){document.getElementById('lv-preid').textContent=preEntry.pre_id;}
  else{document.getElementById('lv-preid').textContent='—';}
  if(sid){
    const qs=(dQ?.sessoes||[]).find(x=>x.session_id===sid);
    if(qs){document.getElementById('lv-al').textContent=qs.nome_aluno;document.getElementById('lv-te').textContent=qs.tema;document.getElementById('lv-sk').textContent=qs.skill;document.getElementById('lv-ac').textContent=qs.acertos+'/'+qs.total_perguntas}
    const hs=dH.find(x=>x.session_id===sid);
    if(hs&&!document.getElementById('lv-al').textContent.replace('-','')){document.getElementById('lv-al').textContent=hs.nome_aluno;document.getElementById('lv-te').textContent=hs.tema||'-';document.getElementById('lv-sk').textContent=hs.skill}
  }
  if(d.status==='quiz')document.getElementById('lv-cp').textContent='Pergunta '+((d.quiz_idx_atual||0)+1)+'/5';
  else if(d.status==='ativo')document.getElementById('lv-cp').textContent='Cena ativa';
  else document.getElementById('lv-cp').textContent='-';
  const el=document.getElementById('lv-cena');
  if(d.status==='ativo'&&d.dados&&d.dados.historia_original){el.innerHTML=`<strong style="font-size:.85rem;color:var(--primary)">Narrativa atual:</strong><p style="font-size:.85rem;line-height:1.6;margin-top:.4rem">${(d.dados.historia_original||'').substring(0,500)}</p>${d.dados.opcoes?.length?`<div style="margin-top:.75rem">${d.dados.opcoes.map(o=>`<span class="opcao-hist">${o}</span>`).join('')}</div>`:''}`}
  else if(d.status==='quiz'&&d.dados&&d.dados.pergunta){el.innerHTML=`<strong style="font-size:.85rem;color:var(--primary)">Pergunta do quiz:</strong><p style="font-size:.9rem;font-weight:600;margin-top:.4rem">${d.dados.pergunta}</p>`}
  else{el.textContent='Aguardando sessao ao vivo...'}
}

async function exportarExcel(){try{const r=await fetch(API+'/exportar_excel');if(!r.ok){const e=await r.json();alert('Erro: '+e.msg);return}const blob=await r.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='storytelling_'+new Date().toISOString().slice(0,10)+'.xlsx';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url)}catch(e){alert('Erro: '+e.message)}}

async function exportarExcelAnalista(){try{const r=await fetch(API+'/exportar_analista');if(!r.ok){const e=await r.json();alert('Erro: '+e.msg);return}const blob=await r.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='analise_completa_'+new Date().toISOString().slice(0,10)+'.xlsx';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url)}catch(e){alert('Erro: '+e.message)}}

let dP=[], dPStats={};
let pSK='data_hora', pSA=false;

async function fP(){
  try{
    const [r1,r2]=await Promise.all([fetch(API+'/fila_participantes'),fetch(API+'/estatisticas_participacao')]);
    if(r1.ok)dP=await r1.json();
    if(r2.ok)dPStats=await r2.json();
    uiP();
  }catch(e){}
}

function uiP(){
  const t=new Date().toLocaleTimeString('pt-BR');
  document.getElementById('p-lu').textContent=t;
  document.getElementById('p-total-pre').textContent=dPStats.total_pre||0;
  document.getElementById('p-total-hist').textContent=dPStats.total_historia||0;
  document.getElementById('p-total-pos').textContent=dPStats.total_pos||0;
  document.getElementById('p-total-des').textContent=dPStats.total_desistiu||0;
  document.getElementById('p-aguardando').textContent=dPStats.aguardando_historia||0;
  renderFilaEspera();
  renderPT();
}

function renderFilaEspera(){
  const aguardando=(dP||[]).filter(p=>p.status==='aguardando_historia');
  const el=document.getElementById('fila-cards');
  if(!aguardando.length){
    el.innerHTML='<div style="color:var(--muted);font-size:.875rem">Nenhum participante aguardando.</div>';
    return;
  }
  el.innerHTML=aguardando.map(p=>`
    <div class="fila-card aguardando">
      <div>
        <div class="fila-id" style="color:var(--amber)">${p.pre_id}</div>
        <div class="fila-label">Aguardando sess\u00e3o</div>
        <div style="font-size:.7rem;color:var(--muted);margin-top:2px">${fmt(p.data_hora)}</div>
      </div>
    </div>`).join('');
}

const STATUS_LABELS={
  'aguardando_historia':'Aguardando sess\u00e3o',
  'em_historia':'Em sess\u00e3o',
  'historia_concluida':'Hist\u00f3ria conclu\u00edda',
  'pos_respondido':'P\u00f3s respondido',
  'desistiu':'Desistiu',
  'sem_estudo':'Sem estudo'
};

function renderPT(){
  const fa=document.getElementById('p-fa').value.toLowerCase();
  const fs=document.getElementById('p-fs').value;
  const res=(dP||[]).filter(p=>{
    if(fa&&!p.pre_id.toLowerCase().includes(fa))return false;
    if(fs&&p.status!==fs)return false;
    return true;
  });
  document.getElementById('p-tt').textContent='Participantes ('+res.length+')';
  document.getElementById('p-cnt').textContent=res.length+' participante(s)';
  document.getElementById('p-emp').style.display=res.length?'none':'block';
  const tb=document.getElementById('p-tb');
  tb.innerHTML=res.map(p=>{
    const sc='ps-'+p.status;
    const sl=STATUS_LABELS[p.status]||p.status;
    return`<tr>
      <td><strong style="font-size:1rem">${p.pre_id}</strong></td>
      <td style="color:var(--muted);font-size:.82rem">${fmt(p.data_hora)}</td>
      <td><span class="part-status ${sc}">${sl}</span></td>
      <td style="color:var(--muted);font-size:.78rem">${p.session_id||'&mdash;'}</td>
    </tr>`;
  }).join('');
}
function limparP(){['p-fa','p-fs'].forEach(id=>{document.getElementById(id).value=''});renderPT();}

function forcarAvancoNao() {
  const btn = document.getElementById('btnContinuarNao');
  if(btn.disabled) return;
  
  btn.disabled = true;
  const originalText = btn.innerHTML;
  btn.innerHTML = `<i data-lucide="hourglass" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i> Aguarde 5s...`;
  btn.style.opacity = "0.5";
  btn.style.cursor = "not-allowed";
  
  fetch('http://127.0.0.1:5000/forcar_avanco', { method: 'POST' })
    .catch(e => console.error("Erro ao forçar avanço:", e));

  setTimeout(() => {
      btn.disabled = false;
      btn.innerHTML = originalText;
      btn.style.opacity = "1";
      btn.style.cursor = "pointer";
  }, 5000);
}

async function poll(){
  await Promise.all([fQ(),fH(),fL(),fL_pesquisa(),fP()]);
  if(qExp){delete cQ[qExp];const el=document.getElementById('qd-'+qExp);if(el)await fQD(qExp)}
  if(hExp){delete cH[hExp];const el=document.getElementById('hd-'+hExp);if(el)await fHD(hExp)}
}
poll();setInterval(poll,POLL);
