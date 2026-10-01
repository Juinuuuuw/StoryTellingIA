
        const SERVER_IP = window.location.hostname || "127.0.0.1";
        const API_URL = `http://${SERVER_IP}:5000`;
        const ROBOT_URL = "http://localhost:8080";

        // Captura o pre_id da URL query string (?pre_id=Q1) — funciona como fallback/atalho
        const _urlParams = new URLSearchParams(window.location.search);
        let lastPreId = _urlParams.get('pre_id') || null;

        // Se o pre_id já veio pela URL, pula o step de identificação automaticamente
        if (lastPreId) {
            document.addEventListener('DOMContentLoaded', () => {
                mostrarStep('step-nome');
            });
        }

        let lastSessionId = null;
        let lastHistoryText = null;
        let currentSequenceId = 0;
        let isModalLocallyOpen = false;
        let typeWriterTimeout = null;


        function typeWriterEffect(text, element) {
            if (typeWriterTimeout) clearTimeout(typeWriterTimeout);
            element.innerHTML = '';
            let i = 0;
            function type() {
                if (i < text.length) {
                    element.innerHTML += text.charAt(i);
                    i++;
                    typeWriterTimeout = setTimeout(type, 30);
                }
            }
            type();
        }

        /**
         * splitByCharLength — divide o texto em N chunks de tamanho equilibrado.
         *
         * Regras:
         *  1. Só corta em ponto final (.  !  ?) — nunca no meio de uma frase.
         *  2. Distribui as frases tentando que cada chunk tenha ~igual nº de caracteres.
         *  3. Garante que nenhum chunk fique vazio:
         *     - Se há menos frases que chunks, o último chunk é dividido em partes menores.
         *     - Qualquer fragmento sem pontuação terminal vai para o último chunk.
         */
        function splitByCharLength(text, numChunks) {
            if (!text || numChunks <= 0) return [text || ''];

            // Captura frases terminadas em . ! ? (incluindo aspas/parênteses logo após)
            // Ex: "Disse ela." / "Isso é incrível!" / "O que aconteceu?"
            const rawSentences = text.match(/[^.!?]+[.!?]["')\]]?(?:\s|$)/g) || [];
            const sentences = rawSentences.map(s => s.trim()).filter(s => s.length > 0);

            // Texto que sobrou sem pontuação terminal (ex: última frase sem ponto)
            const matched = rawSentences.join('');
            const orphan = text.slice(matched.length).trim();

            // Se não conseguiu detectar frases, devolve o texto inteiro em todos os chunks
            if (sentences.length === 0) {
                return Array(numChunks).fill(text);
            }

            // Se há apenas uma frase para vários chunks, distribui por palavras
            if (sentences.length === 1 && numChunks > 1) {
                const words = sentences[0].split(/\s+/);
                const perChunk = Math.ceil(words.length / numChunks);
                const chunks = [];
                for (let i = 0; i < numChunks; i++) {
                    const part = words.slice(i * perChunk, (i + 1) * perChunk).join(' ');
                    if (part) chunks.push(part);
                }
                while (chunks.length < numChunks) chunks.push(chunks[chunks.length - 1] || '');
                return chunks;
            }

            // Calcula o alvo de caracteres por chunk
            const totalChars = sentences.reduce((acc, s) => acc + s.length, 0)
                               + (orphan ? orphan.length : 0);
            const targetPerChunk = totalChars / numChunks;

            const chunks = [];
            let bucket   = [];
            let bucketLen = 0;
            let sIdx     = 0;

            for (let chunkIdx = 0; chunkIdx < numChunks; chunkIdx++) {
                const isLast      = chunkIdx === numChunks - 1;
                const sentencesLeft = sentences.length - sIdx;
                const chunksLeft  = numChunks - chunkIdx;

                bucket    = [];
                bucketLen = 0;

                // Último chunk: absorve tudo que sobrou
                if (isLast) {
                    while (sIdx < sentences.length) {
                        bucket.push(sentences[sIdx++]);
                    }
                    if (orphan) bucket.push(orphan);
                    chunks.push(bucket.join(' ').trim());
                    break;
                }

                // Garante pelo menos 1 frase por chunk, reservando 1 frase para cada chunk futuro
                const minRequired = chunksLeft - 1; // outros chunks também precisam de pelo menos 1
                const available   = sentencesLeft - minRequired;

                // Adiciona frases até atingir o alvo de caracteres
                let added = 0;
                while (sIdx < sentences.length && added < available) {
                    // Adiciona a primeira frase incondicionalmente
                    if (added === 0) {
                        bucket.push(sentences[sIdx]);
                        bucketLen += sentences[sIdx].length;
                        sIdx++;
                        added++;
                        continue;
                    }

                    const nextLen = sentences[sIdx].length;
                    // Para de adicionar se já ultrapassou o alvo por mais de 20%
                    if (bucketLen + nextLen > targetPerChunk * 1.2 && added >= 1) break;

                    bucket.push(sentences[sIdx]);
                    bucketLen += nextLen;
                    sIdx++;
                    added++;
                }

                chunks.push(bucket.join(' ').trim());
            }

            return chunks;
        }

        // ─── CADASTRO / REGISTRO ─────────────────────────────────────────

        let cadNome = '';
        let cadGenero = '';
        let cadSkill = '';
        let cadTema = '';

        const PERGUNTAS_PERSONAGEM = [
            {
                chave: 'comprimento',
                pergunta: 'Qual o tamanho do seu cabelo?',
                cols: 4,
                opcoes: [
                    { label: 'Curto', emoji: `<i data-lucide="scissors" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>`, tag: 'short' },
                    { label: 'Médio', emoji: `<i data-lucide="scissors" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>`, tag: 'medium length' },
                    { label: 'Longo', emoji: `<i data-lucide="waves" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>`, tag: 'long' },
                    { label: 'Preso', emoji: `<i data-lucide="gift" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>`, tag: 'ponytail' }
                ]
            },
            {
                chave: 'tipo',
                pergunta: 'Como é o tipo do seu cabelo?',
                cols: 4,
                opcoes: [
                    { label: 'Liso', emoji: `<i data-lucide="minus" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>`, tag: 'straight' },
                    { label: 'Ondulado', emoji: `<i data-lucide="activity" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>`, tag: 'wavy' },
                    { label: 'Cacheado', emoji: `<i data-lucide="hurricane" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>`, tag: 'curly' },
                    { label: 'Crespo', emoji: `<i data-lucide="circle-dot" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>`, tag: 'coily' }
                ]
            },
            {
                chave: 'cor_cabelo',
                pergunta: 'Qual é a cor do seu cabelo?',
                cols: 4,
                opcoes: [
                    { label: 'Preto', emoji: `<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:#2d3748; fill:#2d3748;"></i>`, tag: 'black hair' },
                    { label: 'Castanho', emoji: `<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:#744210; fill:#744210;"></i>`, tag: 'brown hair' },
                    { label: 'Loiro', emoji: `<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:#ecc94b; fill:#ecc94b;"></i>`, tag: 'blonde hair' },
                    { label: 'Ruivo', emoji: `<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:#e53e3e; fill:#e53e3e;"></i>`, tag: 'red hair' }
                ]
            },
            {
                chave: 'pele',
                pergunta: 'Qual é a cor da sua pele?',
                cols: 4,
                opcoes: [
                    { label: 'Clara', emoji: `<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:#fff5f5; fill:#fff5f5;"></i>`, tag: 'light skin' },
                    { label: 'Morena', emoji: `<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:#975a16; fill:#975a16;"></i>`, tag: 'tanned skin' },
                    { label: 'Negra', emoji: `<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:#2d3748; fill:#2d3748;"></i>`, tag: 'dark skin' },
                    { label: 'Amarelada', emoji: `<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:#fefcbf; fill:#fefcbf;"></i>`, tag: 'pale skin' }
                ]
            },
            {
                chave: 'olhos',
                pergunta: 'E os seus olhos?',
                cols: 4,
                opcoes: [
                    { label: 'Castanhos', emoji: `<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:#975a16; fill:#975a16;"></i>`, tag: 'brown eyes' },
                    { label: 'Verdes', emoji: `<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:#48bb78; fill:#48bb78;"></i>`, tag: 'green eyes' },
                    { label: 'Azuis', emoji: `<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:#4299e1; fill:#4299e1;"></i>`, tag: 'blue eyes' },
                    { label: 'Escuros', emoji: `<i data-lucide="circle" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px; color:#1a202c; fill:#1a202c;"></i>`, tag: 'dark eyes' }
                ]
            }
        ];

        let perguntaPersonagemAtual = 0;
        const respostasPersonagem = {};

        function mostrarStep(id) {
            document.querySelectorAll('.cadastro-step').forEach(s => s.classList.remove('ativo'));
            document.getElementById(id).classList.add('ativo');
            gsap.fromTo('.cadastro-box', { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, ease: 'power2.out' });
        }

        function validarStepNome() {
            cadNome = document.getElementById('input-nome').value.trim();
            document.getElementById('btn-nome').disabled = cadNome.length < 2;
        }

        // ─── STEP PRÉ-ID ────────────────────────────────────────────────

        function validarStepPreId() {
            const val = document.getElementById('input-preid').value.trim();
            // Aceita formato Qn (ex: Q1, Q12)
            const ok = /^Q\d+$/i.test(val);
            document.getElementById('btn-preid-confirmar').disabled = !ok;
        }

        async function confirmarPreId() {
            const val = document.getElementById('input-preid').value.trim().toUpperCase();
            if (!/^Q\d+$/.test(val)) return;

            // Consulta o servidor para verificar se o ID existe
            try {
                const resp = await fetch(`${API_URL}/pre_questionario_dados?pre_id=${val}`);
                if (resp.ok) {
                    const dados = await resp.json();
                    lastPreId = val;
                    // Mostra badge de confirmação
                    document.getElementById('preid-badge-val').textContent = val;
                    document.getElementById('preid-badge').style.display = 'block';
                    document.getElementById('btn-preid-confirmar').textContent = '✓ CONFIRMADO — CONTINUAR →';
                    document.getElementById('btn-preid-confirmar').onclick = () => mostrarStep('step-nome');
                    document.getElementById('btn-preid-confirmar').disabled = false;
                    document.getElementById('btn-preid-confirmar').style.background = 'linear-gradient(135deg, #059669, #10B981)';
                } else {
                    // ID não encontrado
                    document.getElementById('input-preid').style.border = '2px solid #EF4444';
                    document.getElementById('input-preid').placeholder = 'Código não encontrado. Tente novamente.';
                    document.getElementById('input-preid').value = '';
                    document.getElementById('btn-preid-confirmar').disabled = true;
                    setTimeout(() => {
                        document.getElementById('input-preid').style.border = '';
                        document.getElementById('input-preid').placeholder = 'Digite seu código (ex: Q1)';
                    }, 2500);
                }
            } catch(e) {
                // Se o servidor não responder, aceita o código informado sem validar
                lastPreId = val;
                document.getElementById('preid-badge-val').textContent = val;
                document.getElementById('preid-badge').style.display = 'block';
                document.getElementById('btn-preid-confirmar').textContent = '✓ CONTINUAR →';
                document.getElementById('btn-preid-confirmar').onclick = () => mostrarStep('step-nome');
                document.getElementById('btn-preid-confirmar').disabled = false;
            }
        }

        function prosseguirSemPreId() {
            lastPreId = null;
            mostrarStep('step-nome');
        }

        function avancarParaGenero() {
            cadNome = document.getElementById('input-nome').value.trim();
            if (cadNome.length < 2) return;
            mostrarStep('step-jornada');
        }

        function selecionarGenero(genero) {
            cadGenero = genero;
            document.getElementById('card-masculino').classList.toggle('selected', genero === 'Masculino');
            document.getElementById('card-feminino').classList.toggle('selected', genero === 'Feminino');
            validarStepJornada();
        }

        function selecionarJornada(skill, tema) {
            cadSkill = skill;
            cadTema = tema;
            document.getElementById('card-turing').classList.toggle('selected', skill === 'alan_turing');
            document.getElementById('card-katherine').classList.toggle('selected', skill === 'katherine_johnson');
            validarStepJornada();
        }

        function validarStepJornada() {
            document.getElementById('btn-jornada').disabled = !(cadGenero && cadSkill);
        }

        function avancarParaPersonagem() {
            if (!cadGenero || !cadSkill) return;
            perguntaPersonagemAtual = 0;
            mostrarStep('step-personagem');
            renderizarPerguntaPersonagem();
        }

        function renderizarPerguntaPersonagem() {
            const p = PERGUNTAS_PERSONAGEM[perguntaPersonagemAtual];
            document.getElementById('personagem-pergunta-titulo').innerText = p.pergunta;
            document.getElementById('btn-personagem').disabled = true;

            const isLast = perguntaPersonagemAtual === PERGUNTAS_PERSONAGEM.length - 1;
            document.getElementById('btn-personagem').innerHTML = isLast ? 'INICIAR JORNADA ✨' : 'CONFIRMAR →';

            const grid = document.getElementById('personagem-opcoes-grid');
            grid.innerHTML = '';
            grid.style.gridTemplateColumns = `repeat(${p.cols}, 1fr)`;

            p.opcoes.forEach((op, idx) => {
                const card = document.createElement('div');
                card.className = 'card-opcao';
                card.innerHTML = `<div class="card-emoji">${op.emoji}</div><div class="card-titulo">${op.label}</div>`;
                const jaRespondido = respostasPersonagem[p.chave];
                if (jaRespondido && jaRespondido.tag === op.tag) card.classList.add('selected');
                card.onclick = () => {
                    respostasPersonagem[p.chave] = op;
                    grid.querySelectorAll('.card-opcao').forEach(c => c.classList.remove('selected'));
                    card.classList.add('selected');
                    document.getElementById('btn-personagem').disabled = false;
                };
                grid.appendChild(card);
            });

            gsap.fromTo('.cadastro-box', { y: 15, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4, ease: 'power2.out' });
        }

        function avancarPersonagem() {
            if (!respostasPersonagem[PERGUNTAS_PERSONAGEM[perguntaPersonagemAtual].chave]) return;
            perguntaPersonagemAtual++;
            if (perguntaPersonagemAtual < PERGUNTAS_PERSONAGEM.length) {
                renderizarPerguntaPersonagem();
            } else {
                iniciarHistoria();
            }
        }

        async function iniciarHistoria() {
            mostrarStep('step-aguardando');

            // Monta a string de visual do personagem
            const r = respostasPersonagem;
            const generoIngles = cadGenero === 'Feminino' ? '1girl' : '1boy';
            let roupaTag = 'period-appropriate clothing';
            if (cadSkill === 'alan_turing') roupaTag = 'casual 1930s clothes, vintage sweater and trousers';
            else if (cadSkill === 'katherine_johnson') roupaTag = cadGenero === 'Feminino' ? 'formal 1960s suit, elegant vintage dress' : 'formal 1960s suit, elegant vintage suit';

            const visualFixo = `${generoIngles}, ${r.comprimento.tag} ${r.tipo.tag} ${r.cor_cabelo.tag}, ${r.pele.tag}, ${r.olhos.tag}, ${roupaTag}`;

            try {
                const resp = await fetch(`${API_URL}/iniciar_historia`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        nome: cadNome,
                        tema: cadTema,
                        skill: cadSkill,
                        genero: cadGenero,
                        visual_fixo: visualFixo
                    })
                });
                const dados = await resp.json();
                if (dados.status === 'sucesso') {
                    lastSessionId = dados.session_id;

                    // ─── Vincula pre_id ao session_id (se veio do pré-questionário) ───
                    if (lastPreId) {
                        fetch(`${API_URL}/atualizar_status_pre`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                pre_id: lastPreId,
                                status: 'em_historia',
                                session_id: lastSessionId
                            })
                        }).catch(() => {});
                    }

                    // Sinaliza ao story_client (daemon) para iniciar a geração de imagens
                    fetch(`${API_URL}/iniciar_daemon`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ session_id: dados.session_id })
                    }).catch(() => {});
                    
                    // Esconde o cadastro e inicia o polling
                    document.getElementById('cadastro-screen').style.display = 'none';
                    document.getElementById('story-panel').style.display = 'block';
                    pollStatus();
                } else {
                    alert('Erro ao iniciar a história. Tente novamente.');
                    mostrarStep('step-nome');
                }
            } catch (e) {
                alert('Não foi possível conectar ao servidor. Verifique se ele está rodando.');
                mostrarStep('step-aguardando');
            }
        }


        async function waitForImage(filename) {
            let currentFilename = filename;
            let attempts = 0;
            while(attempts < 300) {
                try {
                    const res = await fetch(`${API_URL}/check_image/${currentFilename}`, { cache: 'no-store' });
                    const data = await res.json();
                    if (data.ready) return currentFilename;
                } catch(e) {}
                
                attempts++;
                if (attempts === 20 && currentFilename.endsWith('.gif')) {
                    currentFilename = currentFilename.replace('.gif', '.png');
                }
                await new Promise(r => setTimeout(r, 1000));
            }
            return null;
        }

        async function startImageSequence(images, data, textChunks) {
            currentSequenceId++;
            const seqId = currentSequenceId;

            const imgEl = document.getElementById('scene-image');
            const loader = document.getElementById('loader');
            const storyTextEl = document.getElementById('story-text');
            
            imgEl.style.display = "block";

            const playFrame = async (idx) => {
                const filename = images[idx];
                const finalFilename = await waitForImage(filename);
                if (seqId !== currentSequenceId) return false;
                
                if (finalFilename) {
                    const url = `${API_URL}/images/${finalFilename}`;
                    // Força o carregamento da imagem silenciosamente antes de exibir
                    const img = new Image();
                    await new Promise(res => { img.onload = res; img.onerror = res; img.src = url; });
                    
                    // Ocultar loader apenas quando a 1ª imagem for exibida
                    if (idx === 0) {
                        loader.style.display = 'none';
                    }

                    // Notifica o servidor que este quadro está visível agora (NAO sincroniza a fala)
                    fetch(`${API_URL}/publicar_quadro`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ quadro_idx: idx })
                    }).catch(() => {});

                    imgEl.src = url;
                    if (textChunks && textChunks[idx]) {
                        typeWriterEffect(textChunks[idx], storyTextEl);
                    }
                    // Efeito Ken Burns Cinematico
                    gsap.fromTo(imgEl,
                        { scale: 1.05, x: 0, y: 0, opacity: 0.2 },
                        { scale: 1.15, x: 10, y: -10, opacity: 1, duration: 10, ease: "sine.inOut" }
                    );
                    return true;
                }
                return false;
            };

            // ── Aguarda o Dashboard mandar avançar (Botão Continuar) ──────────
            const waitForDashboardSignal = async () => {
                // localAvanco captura o step no momento que a imagem carregou
                const waitStep = window.currentAvancoStep || 0;
                while (true) {
                    if ((window.currentAvancoStep || 0) > waitStep) {
                        return; // O dashboard aumentou o avanço!
                    }
                    await new Promise(r => setTimeout(r, 500));
                }
            };

            if (images.length === 0) { triggerDecisionModal(data); return; }

            for (let i = 0; i < images.length; i++) {
                if (seqId !== currentSequenceId) return;
                await playFrame(i);

                // Em vez de esperar pelo tempo matematicamente, agora espera o analista clicar
                await waitForDashboardSignal();

                if (i < images.length - 1) {
                    // pequena pausa de transição (fôlego)
                    await new Promise(r => setTimeout(r, 400));
                } else {
                    if (seqId === currentSequenceId) {
                        triggerDecisionModal(data);
                        if (data.tem_opcoes === false || !data.opcoes || data.opcoes.length === 0) {
                            // Fim da história: avisa o backend para encerrar a sessão
                            fetch(`${API_URL}/finalizar_sessao`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ session_id: lastSessionId })
                            }).catch(() => {});
                        }
                    }
                }
            }
        }

        function triggerDecisionModal(data) {
            if (data.tem_opcoes !== false && data.opcoes && data.opcoes.length > 0) {
                showModal({
                    pergunta: "QUAL É A SUA DECISÃO?",
                    opcoes: data.opcoes
                });
            }
        }

        function showModal(data) {
            isModalLocallyOpen = true;
            const modalEl = document.getElementById('interaction-modal');
            const modalBox = modalEl.querySelector('.modal-box');
            
            modalEl.style.display = 'flex';
            document.getElementById('modal-question').innerText = data.pergunta;
            
            gsap.fromTo(modalBox, { scale: 0.9, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.6, ease: "power3.out" });
            
            const optsContainer = document.getElementById('modal-options');
            optsContainer.innerHTML = '';
            optsContainer.style.pointerEvents = 'auto'; // RESET POINTER EVENTS HERE
            
            if (data.opcoes) {
                data.opcoes.forEach((opt, idx) => {
                    const btn = document.createElement('div');
                    btn.className = 'choice-btn';
                    btn.innerText = opt;
                    btn.onclick = async () => {
                        optsContainer.style.pointerEvents = 'none';
                        btn.style.background = 'var(--accent)';
                        btn.style.color = '#000';
                        
                        try {
                            await fetch(`${API_URL}/definir_pensando`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ frase: "Processando sua escolha..." })
                            });
                            hideModal();
                            const loader = document.getElementById('loader');
                            loader.style.display = 'flex';
                            loader.querySelector('div:last-child').innerText = "GERANDO PRÓXIMA CENA...";
                            
                            const resp = await fetch(`${API_URL}/escolher`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ session_id: lastSessionId, escolha_idx: idx, escolha_texto: opt })
                            });
                            const dados = await resp.json();
                            

                        } catch(e) {
                            console.error(e);
                        }
                    };
                    optsContainer.appendChild(btn);
                });
            }
        }

        function hideModal() {
            document.getElementById('interaction-modal').style.display = 'none';
            isModalLocallyOpen = false;
        }

        function splitByCharLength(text, numChunks) {
            if (!text) return Array(numChunks).fill("");
            
            // Divide a frase a cada ponto final, exclamação ou interrogação
            const regex = /[^.!?]+[.!?]+/g;
            let sentences = text.match(regex);
            
            // Fallback se não encontrar pontuação
            if (!sentences || sentences.length === 0) {
                sentences = [text];
            } else {
                // Junta qualquer resto de string que não tinha pontuação no final
                const lastMatchEnd = text.lastIndexOf(sentences[sentences.length - 1]) + sentences[sentences.length - 1].length;
                const remainder = text.slice(lastMatchEnd).trim();
                if (remainder) {
                    sentences[sentences.length - 1] += " " + remainder;
                }
            }
            
            const chunks = [];
            
            // Se houver menos ou igual número de frases que chunks, coloca 1 frase por chunk (e vazios no final)
            // Mas para evitar chunks vazios no final (que quebram a cena 3 quadro 4), dividimos a última frase
            if (sentences.length < numChunks) {
                // Primeiro coloca as frases inteiras
                for (let i = 0; i < sentences.length; i++) {
                    chunks.push(sentences[i].trim());
                }
                // Preenche o resto com vazio inicialmente
                while (chunks.length < numChunks) {
                    chunks.push("");
                }
                // Tenta emprestar palavras do último chunk não-vazio para preencher os vazios
                for (let i = chunks.length - 1; i > 0; i--) {
                    if (!chunks[i]) {
                        // Encontra o chunk anterior não-vazio com mais de 2 palavras
                        for (let j = i - 1; j >= 0; j--) {
                            let words = chunks[j].split(/\s+/);
                            if (words.length > 2) {
                                let half = Math.floor(words.length / 2);
                                chunks[i] = words.slice(half).join(" ") + (words.slice(half).join("").match(/[.!?]/) ? "" : ".");
                                chunks[j] = words.slice(0, half).join(" ") + "...";
                                break;
                            }
                        }
                    }
                }
                return chunks;
            }
            
            // Se tem mais frases do que chunks, agrupa por quantidade de caracteres (preservando frases completas)
            const totalChars = sentences.reduce((acc, s) => acc + s.length, 0);
            const targetCharsPerChunk = Math.max(1, Math.floor(totalChars / numChunks));
            
            let currentChunk = "";
            let currentChars = 0;

            for (let i = 0; i < sentences.length; i++) {
                const s = sentences[i].trim();
                if (currentChars + s.length > targetCharsPerChunk && chunks.length < numChunks - 1 && currentChunk.length > 0) {
                    chunks.push(currentChunk.trim());
                    currentChunk = s;
                    currentChars = s.length;
                } else {
                    currentChunk += (currentChunk ? " " : "") + s;
                    currentChars += s.length;
                }
            }
            if (currentChunk) {
                chunks.push(currentChunk.trim());
            }

            while (chunks.length < numChunks) {
                chunks.push(""); 
            }
            
            return chunks;
        }

        async function checkActiveSession() {
            if (isModalLocallyOpen) return;
            try {
                const r = await fetch(`${API_URL}/visualizador/cena_atual`, { cache: 'no-store' });
                const data = await r.json();

                if (data.status === "aguardando" || data.status === "pensando") {
                    document.getElementById('loader').style.display = 'flex';
                    if (!isModalLocallyOpen && data.status === "aguardando") {
                        document.getElementById('loader').querySelector('div:last-child').innerText = "AGUARDANDO O NAO...";
                    } else if (data.status === "pensando") {
                        document.getElementById('loader').querySelector('div:last-child').innerText = "CRIANDO PRÓXIMA CENA...";
                    }
                    return;
                }

                if (data.status === "modal") {
                    document.getElementById('loader').style.display = 'none';
                    const modalData = data.dados || data;
                    if (!isModalLocallyOpen || document.getElementById('modal-question').innerText !== modalData.pergunta) {
                        showModal({
                            pergunta: modalData.pergunta,
                            opcoes: modalData.opcoes
                        });
                    }
                    return;
                }

                // 🔹 Quiz: gerando 🔹
                if (data.status === "quiz_gerando") {
                    document.getElementById('loader').style.display = 'flex';
                    document.getElementById('loader').querySelector('div:last-child').innerText = "PREPARANDO PERGUNTAS...";
                    hideModal();
                    return;
                }

                // 🔹 Quiz: pergunta atual (Obsoleto, agora é no pós-questionário) 🔹
                if (data.status === "quiz") {
                    return;
                }

                // ── História Finalizada ──
                if (data.status === "historia_fim" || data.status === "quiz_fim") {
                    if (!window.historiaFinalizada) {
                        window.historiaFinalizada = true;
                        
                        // Oculta loader e qualquer modal
                        document.getElementById('loader').style.display = 'none';
                        document.getElementById('quiz-modal').style.display = 'none';
                        hideModal();
                        
                        // Mostra a tela de Fim de Sessão
                        const fimScreen = document.getElementById('quiz-fim-screen');
                        fimScreen.style.display = 'flex';
                        gsap.fromTo(fimScreen, { opacity: 0 }, { opacity: 1, duration: 1, ease: "power2.out" });
                        
                        document.getElementById('quiz-fim-badge').innerHTML = `✨`;
                        document.getElementById('quiz-fim-titulo').innerText = "Obrigado por ouvir a história!";
                        document.getElementById('quiz-fim-subtitulo').innerText = "A história terminou. Você pode fechar esta tela e o seu pesquisador te guiará para a próxima etapa.";
                    }
                    return;
                }

                // Status ATIVO
                const sceneData = data.dados || data;
                
                // ATUALIZA A VARIÁVEL DE AVANÇO MANUAL
                window.currentAvancoStep = data.avanco_step || 0;

                const textoHistoria = sceneData.historia_original || sceneData.historia || "";
                
                if (data.session_id !== lastSessionId || textoHistoria !== lastHistoryText) {
                    lastSessionId = data.session_id;
                    lastHistoryText = textoHistoria;

                    hideModal();
                    document.getElementById('loader').style.display = 'flex'; // mantem loader até imagem 1 carregar
                    
                    const storyTextEl = document.getElementById('story-text');
                    
                    const hasImages = Array.isArray(sceneData.imagens_arquivos) && sceneData.imagens_arquivos.length > 0;
                    if (hasImages) {
                        const numChunks = sceneData.imagens_arquivos.length;
                        const textChunks = splitByCharLength(textoHistoria, numChunks);
                        
                        // Registra os text_chunks no servidor UMA ÚNICA VEZ para o NAO sincronizar.
                        // Usa endpoint dedicado para não interferir no status/quadro_atual da cena.
                        fetch(`${API_URL}/registrar_chunks`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ text_chunks: textChunks })
                        }).catch(() => {});

                        startImageSequence(sceneData.imagens_arquivos, sceneData, textChunks);
                    } else {
                        typeWriterEffect(textoHistoria, storyTextEl);
                        document.getElementById('loader').style.display = 'none';
                        triggerDecisionModal(sceneData);
                    }
                }
            } catch (err) {
                console.log("Erro ao sincronizar:", err);
            }
        }

        // ─── QUIZ FUNCTIONS ───────────────────────────────────────────────

        let quizRespondidaAtual = false;

        function showQuizModal(sessionId, perguntaId, dadosPergunta, numAtual, total) {
            quizRespondidaAtual = false;

            document.getElementById('quiz-progress').innerText = `Pergunta ${numAtual} de ${total}`;
            document.getElementById('quiz-question').innerText = dadosPergunta.pergunta;

            const optsContainer = document.getElementById('quiz-options');
            optsContainer.innerHTML = '';

            const quizModal = document.getElementById('quiz-modal');
            quizModal.style.display = 'flex';

            gsap.fromTo(quizModal.querySelector('.quiz-box'),
                { scale: 0.92, opacity: 0 },
                { scale: 1, opacity: 1, duration: 0.5, ease: "power3.out" }
            );

            dadosPergunta.opcoes.forEach((opt, idx) => {
                const btn = document.createElement('button');
                btn.className = 'quiz-btn';
                btn.innerText = opt;
                btn.onclick = () => respondirQuiz(sessionId, perguntaId, idx, btn, optsContainer);
                optsContainer.appendChild(btn);
            });
        }

        async function respondirQuiz(sessionId, perguntaId, respostaIdx, btnClicado, optsContainer) {
            if (quizRespondidaAtual) return;
            quizRespondidaAtual = true;

            // Bloqueia todos os botões imediatamente
            optsContainer.querySelectorAll('.quiz-btn').forEach(b => b.disabled = true);

            // Envia resposta ao servidor
            try {
                await fetch(`${API_URL}/responder_quiz`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessionId,
                        pergunta_id: perguntaId,
                        resposta_idx: respostaIdx
                    })
                });
            } catch(e) {
                console.error("Erro ao enviar resposta do quiz:", e);
            }

            // Aguarda 1.5s antes de liberar o polling para detectar a próxima pergunta
            await new Promise(r => setTimeout(r, 1500));
            document.getElementById('quiz-question').innerText = "..."; // reset para o polling detectar mudança
        }

        function showQuizFim(resultado) {
            document.getElementById('quiz-modal').style.display = 'none';
            document.getElementById('loader').style.display = 'none';

            const fimScreen = document.getElementById('quiz-fim-screen');
            fimScreen.style.display = 'flex';
            gsap.fromTo(fimScreen, { opacity: 0 }, { opacity: 1, duration: 1, ease: "power2.out" });

            if (resultado) {
                const acertos = resultado.acertos || 0;
                const total = resultado.total_perguntas || 5;
                const nome = resultado.nome_aluno || "Explorador";
                const pct = resultado.percentual || 0;

                document.getElementById('quiz-fim-badge').innerHTML = `${acertos} / ${total}`;

                let titulo = "Parabéns!";
                let subtitulo = `${nome}, você completou a jornada histórica!`;

                if (pct === 100) {
                    titulo = "Perfeito! 🌟";
                    subtitulo = `${nome}, acertou tudo! Você é um verdadeiro explorador da história!`;
                } else if (pct >= 66) {
                    titulo = `Muito bem! <i data-lucide="thumbs-up" style="width:1.2em; height:1.2em; display:inline-block; vertical-align:-0.2em; margin-right:4px;"></i>`;
                    subtitulo = `${nome}, você conhece bem a história!`;
                } else if (pct >= 33) {
                    titulo = "Bom trabalho!";
                    subtitulo = `${nome}, continue explorando para aprender mais!`;
                } else {
                    titulo = "Continue tentando!";
                    subtitulo = `${nome}, cada jornada é uma nova oportunidade de aprender!`;
                }

                document.getElementById('quiz-fim-titulo').innerText = titulo;
                document.getElementById('quiz-fim-subtitulo').innerText = subtitulo;
            }

            // Após 4 segundos, transiciona para o questionário Likert
            setTimeout(() => {
                window.location.href = `/pos_questionario?pre_id=${lastPreId || ''}&session_id=${lastSessionId || ''}`;
            }, 4000);
        }

        // ─── QUESTIONÁRIO LIKERT ───────────────────────────────────────────

        const LIKERT_SECOES = [
            {
                titulo: "Imersão Narrativa",
                desc: "",
                tipo: "escala",
                perguntas: [
                    { texto: "Consegui imaginar facilmente os acontecimentos apresentados na história.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                    { texto: "Enquanto ouvia a história, deixei de prestar atenção, por alguns momentos, no que estava ao meu redor.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                    { texto: "Fiquei mentalmente envolvido(a) com a história.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                    { texto: "A história despertou alguma reação emocional em mim.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                ]
            },
            {
                titulo: "Engajamento com a Experiência",
                desc: "",
                tipo: "escala",
                perguntas: [
                    { texto: "A experiência prendeu minha atenção.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                    { texto: "Gostei de acompanhar a experiência.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                    { texto: "Fiquei curioso(a) para saber o que aconteceria em seguida.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                ]
            },
            {
                titulo: "Interação com o NAO",
                desc: "",
                tipo: "escala",
                perguntas: [
                    { texto: "Consegui compreender claramente o que o NAO dizia.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                    { texto: "Os movimentos e gestos do NAO combinaram com a história.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                    { texto: "A troca de falas com o NAO ocorreu de forma fluida.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                ]
            },
            {
                titulo: "Contribuição das Imagens",
                desc: "",
                tipo: "escala",
                perguntas: [
                    { texto: "As imagens ajudaram a compreender e imaginar os acontecimentos da história.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                    { texto: "As imagens tornaram a experiência mais envolvente.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                ]
            },
            {
                titulo: "Personalização e Adaptação Percebida",
                desc: "",
                tipo: "escala",
                perguntas: [
                    { texto: "Senti que a história considerou o que aconteceu durante minha interação com o NAO.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                    { texto: "Tive a impressão de que minhas respostas ou ações influenciaram a experiência.", labelEsq: "Discordo totalmente", labelDir: "Concordo totalmente" },
                ]
            },
            {
                titulo: "Percepção da Geração Dinâmica",
                desc: "",
                tipo: "escala",
                perguntas: [
                    { texto: "Na sua percepção, a história estava pronta antes da sessão ou foi gerada ou adaptada durante a interação?", labelEsq: "Tenho certeza de que já estava pronta", labelDir: "Tenho certeza de que foi gerada ou adaptada durante a interação" },
                    { texto: "Na sua percepção, as imagens estavam prontas antes da sessão ou foram geradas durante a interação?", labelEsq: "Tenho certeza de que já estavam prontas", labelDir: "Tenho certeza de que foram geradas durante a interação" },
                ]
            },
            {
                titulo: "Percepção do NAO Após a Interação",
                desc: "Agora, considerando toda a experiência que você acabou de realizar com o NAO, indique sua impressão sobre ele. Em cada linha existem duas características opostas. Marque um valor entre 1 e 5.",
                tipo: "grid",
                grupos: [
                    {
                        subtitulo: "Antropomorfismo",
                        linhas: ["Falso / Natural", "Com aspecto mecânico / Com aspecto humano", "Inconsciente / Consciente", "Artificial / Realista", "Move-se com rigidez / Move-se com fluidez"]
                    },
                    {
                        subtitulo: "Animacidade",
                        linhas: ["Morto / Com vida", "Parado / Enérgico", "Artificial / Realista", "Estático / Interativo", "Apático / Participativo"]
                    },
                    {
                        subtitulo: "Simpatia",
                        linhas: ["Não gosto / Gosto", "Hostil / Amigável", "Antipático / Gentil", "Desagradável / Agradável", "Horrível / Simpático"]
                    },
                    {
                        subtitulo: "Inteligência Percebida",
                        linhas: ["Incompetente / Competente", "Ignorante / Sabedor", "Irresponsável / Responsável", "Pouco inteligente / Inteligente", "Insensato / Sensato"]
                    },
                    {
                        subtitulo: "Segurança Percebida",
                        linhas: ["Ansioso / Descontraído", "Calmo / Agitado", "Sereno / Surpreendido"]
                    }
                ]
            },
            {
                titulo: "Expectativa e Experiência",
                desc: "",
                tipo: "escala",
                perguntas: [
                    { texto: "Considerando suas expectativas antes da sessão, como você avalia a experiência realizada?", labelEsq: "Muito abaixo do que eu esperava", labelDir: "Muito acima do que eu esperava" },
                ]
            }
        ];

        let likertSecaoAtual = 0;
        const likertRespostas = {};

        function iniciarLikert() {
            likertSecaoAtual = 0;
            document.getElementById('likert-screen').style.display = 'flex';
            gsap.fromTo('#likert-screen', { opacity: 0 }, { opacity: 1, duration: 0.8, ease: "power2.out" });
            renderizarSecaoLikert();
        }

        function renderizarSecaoLikert() {
            const totalSecoes = LIKERT_SECOES.length;
            const secao = LIKERT_SECOES[likertSecaoAtual];
            const secaoNum = likertSecaoAtual + 1;

            document.getElementById('likert-progress').innerText = `Seção ${secaoNum} de ${totalSecoes}`;
            document.getElementById('likert-section-title').innerText = secao.titulo;
            document.getElementById('likert-section-desc').innerText = secao.desc || '';

            const container = document.getElementById('likert-questions-container');
            container.innerHTML = '';

            if (secao.tipo === 'escala') {
                secao.perguntas.forEach((p, pIdx) => {
                    const chave = `s${likertSecaoAtual}_q${pIdx}`;
                    const block = document.createElement('div');
                    block.className = 'likert-question-block';
                    block.innerHTML = `
                        <div class="likert-question-text">${p.texto}</div>
                        <div class="likert-scale">
                            <span class="likert-label">${p.labelEsq}</span>
                            <div class="likert-buttons" id="btns_${chave}">
                                ${[1,2,3,4,5].map(v => `<button class="likert-btn" onclick="selecionarLikert('${chave}',${v},this)">${v}</button>`).join('')}
                            </div>
                            <span class="likert-label right">${p.labelDir}</span>
                        </div>`;
                    container.appendChild(block);
                });
            } else if (secao.tipo === 'grid') {
                secao.grupos.forEach((grupo, gIdx) => {
                    const header = document.createElement('div');
                    header.style.cssText = 'font-family:"Playfair Display",serif;font-size:1.2rem;color:var(--accent);margin:24px 0 10px;';
                    header.innerText = grupo.subtitulo;
                    container.appendChild(header);

                    const gridDiv = document.createElement('div');
                    gridDiv.className = 'likert-grid';
                    let tableHtml = `<table><thead><tr><th style="text-align:left">Par</th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th></tr></thead><tbody>`;
                    grupo.linhas.forEach((linha, lIdx) => {
                        const chave = `s${likertSecaoAtual}_g${gIdx}_l${lIdx}`;
                        tableHtml += `<tr><td>${linha}</td>${[1,2,3,4,5].map(v => `<td><button class="grid-btn" id="grid_${chave}_${v}" onclick="selecionarGrid('${chave}',${v})">${v}</button></td>`).join('')}</tr>`;
                    });
                    tableHtml += `</tbody></table>`;
                    gridDiv.innerHTML = tableHtml;
                    container.appendChild(gridDiv);
                });
            }

            atualizarBotaoLikert();
            gsap.fromTo('.likert-box', { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, ease: "power2.out" });
        }

        function selecionarLikert(chave, valor, btn) {
            likertRespostas[chave] = valor;
            const container = btn.closest('.likert-buttons');
            container.querySelectorAll('.likert-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            atualizarBotaoLikert();
        }

        function selecionarGrid(chave, valor) {
            likertRespostas[chave] = valor;
            [1,2,3,4,5].forEach(v => {
                const b = document.getElementById(`grid_${chave}_${v}`);
                if (b) b.classList.toggle('selected', v === valor);
            });
            atualizarBotaoLikert();
        }

        function secaoRespondida() {
            const secao = LIKERT_SECOES[likertSecaoAtual];
            if (secao.tipo === 'escala') {
                return secao.perguntas.every((_, pIdx) => likertRespostas[`s${likertSecaoAtual}_q${pIdx}`] !== undefined);
            } else if (secao.tipo === 'grid') {
                return secao.grupos.every((grupo, gIdx) =>
                    grupo.linhas.every((_, lIdx) => likertRespostas[`s${likertSecaoAtual}_g${gIdx}_l${lIdx}`] !== undefined)
                );
            }
            return true;
        }

        function atualizarBotaoLikert() {
            document.getElementById('likert-next-btn').disabled = !secaoRespondida();
        }

        function likertNext() {
            likertSecaoAtual++;
            if (likertSecaoAtual < LIKERT_SECOES.length) {
                renderizarSecaoLikert();
                document.querySelector('.likert-box').scrollTop = 0;
            } else {
                // Todas as seções respondidas → tela final
                document.getElementById('likert-screen').style.display = 'none';
                const fim = document.getElementById('fim-screen');
                fim.style.display = 'flex';
                gsap.fromTo(fim, { opacity: 0 }, { opacity: 1, duration: 1.2, ease: "power2.out" });
                console.log("📊 Respostas Likert:", JSON.stringify(likertRespostas));
                
                fetch(`${API_URL}/salvar_likert`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: lastSessionId,
                        respostas: likertRespostas,
                        secoes: LIKERT_SECOES
                    })
                }).catch(e => console.error("Erro ao salvar Likert:", e));

                // ─── Atualiza status do participante para pos_respondido ───
                if (lastPreId) {
                    fetch(`${API_URL}/atualizar_status_pre`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            pre_id: lastPreId,
                            status: 'pos_respondido',
                            session_id: lastSessionId
                        })
                    }).catch(() => {});
                }
            }
        }


        function pollStatus() {
            setInterval(checkActiveSession, 2000);
        }

    