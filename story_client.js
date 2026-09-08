/**
 * story_client.js — MODO DAEMON
 * Roda em background sem nenhum input manual do terminal.
 * Fica polling /daemon_poll até receber uma sessão para processar,
 * então gera todas as imagens e dispara o quiz automaticamente.
 */

const axios = require("axios");
const fs = require("fs");
const path = require("path");

// ─── CONFIGURAÇÃO ─────────────────────────────────────────────
const SERVIDOR_FLASK  = "http://127.0.0.1:5000";
const FORGE_TXT2IMG   = "http://127.0.0.1:7860/sdapi/v1/txt2img";
const POLL_INTERVAL   = 2000; // ms entre cada poll ao servidor

// IP-Adapter: carrega imagem de referência se existir
let base64Referencia = null;
const caminhoReferencia = path.join(__dirname, "referencia.png");
if (fs.existsSync(caminhoReferencia)) {
    base64Referencia = fs.readFileSync(caminhoReferencia).toString("base64");
    console.log("🌟 IP-Adapter ATIVADO: referencia.png carregada.");
} else {
    console.log("⚠️  IP-Adapter inativo: referencia.png não encontrada.");
}

// ─── PASTA DE SESSÃO ──────────────────────────────────────────
let PASTA_SESSAO = "";

function prepararPasta(sessionId) {
    const baseDir = path.join(__dirname, "historias_geradas");
    if (!fs.existsSync(baseDir)) fs.mkdirSync(baseDir);
    PASTA_SESSAO = path.join(baseDir, `sessao_${sessionId}`);
    if (!fs.existsSync(PASTA_SESSAO)) fs.mkdirSync(PASTA_SESSAO);
    console.log(`\n📂 Pasta da sessão: ${PASTA_SESSAO}`);
}

function salvarImagem(base64, nomeArquivo) {
    const filePath = path.join(PASTA_SESSAO, path.basename(nomeArquivo));
    fs.writeFileSync(filePath, Buffer.from(base64, "base64"));
    console.log(`      💾 Salvo: ${filePath}`);
}

function registrarLog(conteudo) {
    const filePath = path.join(PASTA_SESSAO, "historia_completa.txt");
    fs.appendFileSync(filePath, conteudo + "\n");
}

// ─── GERAÇÃO DE IMAGENS ───────────────────────────────────────
async function gerarSequenciaStoryboard(promptsImagens, microcenasTextos, negativePrompt, numeroCena, dadosDaCena, seedCena) {
    console.log(`\n🎨 Gerando Storyboard - Cena ${numeroCena}`);

    for (let i = 0; i < promptsImagens.length; i++) {
        const promptAtual = promptsImagens[i];
        const acaoTexto   = microcenasTextos[i] || `Quadro ${i + 1}`;
        const nomeBase    = dadosDaCena ? dadosDaCena.imagens_arquivos[i] : `cena_${numeroCena}_q${i + 1}.png`;

        console.log(`   🎬 Quadro ${i + 1}: [${acaoTexto}]`);

        const payload = {
            prompt: promptAtual,
            negative_prompt: negativePrompt || "",
            steps: 28,
            width: 768,
            height: 768,
            sampler_name: "DPM++ 2M Karras",
            cfg_scale: 7.0,
            seed: seedCena + (i * 100),
            alwayson_scripts: {},
            override_settings: { CLIP_stop_at_last_layers: 2 }
        };

        if (base64Referencia) {
            payload.alwayson_scripts["controlnet"] = {
                args: [{
                    enabled: true,
                    module: "ip-adapter_clip_sdxl",
                    model: "ip-adapter_sdxl",
                    weight: 0.85,
                    image: base64Referencia,
                    resize_mode: "Crop and Resize",
                    lowvram: false,
                    processor_res: 512,
                    guidance_start: 0.0,
                    guidance_end: 1.0,
                    control_mode: "Balanced"
                }]
            };
        }

        try {
            const response = await axios.post(FORGE_TXT2IMG, payload, { timeout: 300000 });
            if (response.data?.images) {
                const imgBase64 = response.data.images[0];
                salvarImagem(imgBase64, nomeBase);
                registrarLog(`[QUADRO-${i + 1}] ${nomeBase}: ${promptAtual}`);
                if (!base64Referencia) {
                    base64Referencia = imgBase64;
                    console.log("      🌟 IP-Adapter ÂNCORA definida nesta imagem.");
                }
            }
            console.log(`      ✅ Quadro ${i + 1} concluído.`);
        } catch (err) {
            console.log(`      ❌ Erro Quadro ${i + 1}: ${err.message}`);
        }

        // Após o primeiro quadro, publica a cena no frontend
        if (i === 0 && dadosDaCena) {
            axios.post(`${SERVIDOR_FLASK}/publicar_cena`, dadosDaCena).catch(() => {});
        }
    }
}

// ─── COMUNICAÇÃO COM O ROBÔ NAO ───────────────────────────────
async function falarEnrolacao(isInicio, escolhaTexto = "") {
    const frases = isInicio
        ? ["Ajustando meus sensores temporais... Só um momento.", "Acessando os arquivos históricos... Preparando nossa viagem.", "Iniciando os motores de imaginação. Aguarde um instante."]
        : ["Hmm, pensando em como a história continua...", "Calculando as consequências da sua escolha...", "Deixe-me consultar os registros para ver o que acontece agora..."];

    let frase = frases[Math.floor(Math.random() * frases.length)];
    if (!isInicio && escolhaTexto) {
        const conf = ["Então você escolheu", "Interessante... você optou por", "Muito bem, vamos seguir por"];
        frase = `${conf[Math.floor(Math.random() * conf.length)]} ${escolhaTexto}. ${frase}`;
    }

    console.log(`\n🤖 NAO (Pensando): "${frase}"`);
    try {
        await axios.post(`${SERVIDOR_FLASK}/definir_pensando`, { frase });
        await new Promise(r => setTimeout(r, 1500));
    } catch (e) {}
}

// ─── PROCESSAMENTO DE UMA SESSÃO ─────────────────────────────
async function processarSessao(sessionId) {
    console.log(`\n🚀 Iniciando processamento da sessão: ${sessionId}`);

    // Carrega o estado atual da sessão via /status
    let state;
    try {
        const r = await axios.get(`${SERVIDOR_FLASK}/status`);
        state = r.data;
    } catch (e) {
        console.log("❌ Não foi possível obter estado do servidor:", e.message);
        return;
    }

    if (!state || !state.dados) {
        console.log("❌ Estado inválido retornado pelo servidor.");
        return;
    }

    const dados = state.dados;
    const sessionIdReal = state.session_id || sessionId;
    prepararPasta(sessionIdReal);
    base64Referencia = null; // reseta âncora para cada nova sessão

    const seedSessao = parseInt(sessionIdReal) || Math.floor(Math.random() * 1e9);
    let contadorCena = 1;

    registrarLog(`SESSION_ID: ${sessionIdReal}\n`);

    console.log(`\n📖 CENA ${contadorCena}:`);
    console.log(dados.historia_original);
    registrarLog(`\n--- CENA ${contadorCena} ---\n${dados.historia_original}\n`);

    falarEnrolacao(true);

    if (dados.prompts_imagens?.length > 0) {
        await gerarSequenciaStoryboard(dados.prompts_imagens, dados.microcenas_textos, dados.negative_prompt || "", contadorCena, dados, seedSessao);
    } else {
        await axios.post(`${SERVIDOR_FLASK}/publicar_cena`, dados).catch(() => {});
    }

    let temOpcoes = dados.tem_opcoes !== false;

    // ─── LOOP DE ESCOLHAS ──────────────────────────────────────
    while (temOpcoes) {
        console.log("\n👀 Aguardando escolha do jogador...");

        let escolhaTexto = "";
        let idxReal = 0;

        while (true) {
            try {
                const res = await axios.get(`${SERVIDOR_FLASK}/esperar_escolha`);
                if (res.data?.status === "ok") {
                    idxReal      = res.data.dados.escolha_idx;
                    escolhaTexto = res.data.dados.escolha_texto;
                    break;
                }
            } catch (e) {}
            await new Promise(r => setTimeout(r, 1000));
        }

        contadorCena++;
        console.log(`\n⏳ Jogador escolheu: "${escolhaTexto}"`);
        registrarLog(`\nESCOLHA: ${escolhaTexto}`);

        falarEnrolacao(false, escolhaTexto);

        let resposta;
        try {
            const r = await axios.post(`${SERVIDOR_FLASK}/escolher`, {
                session_id: sessionIdReal,
                node_id: null,
                escolha_idx: idxReal,
                escolha_texto: escolhaTexto
            });
            resposta = r.data;
        } catch (e) {
            console.log("❌ Erro ao registrar escolha:", e.message);
            break;
        }

        if (!resposta || resposta.status !== "sucesso") break;

        temOpcoes = resposta.tem_opcoes !== false;

        console.log(`\n📖 CENA ${contadorCena}:`);
        console.log(resposta.historia_original);
        registrarLog(`\n--- CENA ${contadorCena} ---\n${resposta.historia_original}\n`);

        if (resposta.prompts_imagens?.length > 0) {
            await gerarSequenciaStoryboard(resposta.prompts_imagens, resposta.microcenas_textos, resposta.negative_prompt || "", contadorCena, resposta, seedSessao + contadorCena * 1000);
        } else {
            await axios.post(`${SERVIDOR_FLASK}/publicar_cena`, resposta).catch(() => {});
        }

        if (!temOpcoes) console.log("\n🎬 Fim da história!");
    }

    console.log(`\n✨ Sessão encerrada! Arquivos em: ${PASTA_SESSAO}`);

    // Dispara o quiz
    try {
        await axios.post(`${SERVIDOR_FLASK}/finalizar_sessao`, { session_id: sessionIdReal });
        console.log("✅ Quiz solicitado ao servidor.");
    } catch (e) {
        console.log("⚠️  Não foi possível acionar o quiz:", e.message);
    }
}

// ─── LOOP PRINCIPAL DO DAEMON ─────────────────────────────────
async function daemonLoop() {
    console.log("\n==================================================");
    console.log("🤖 NAO — STORY CLIENT DAEMON");
    console.log("==================================================");
    console.log(`Polling ${SERVIDOR_FLASK}/daemon_poll a cada ${POLL_INTERVAL}ms...`);
    console.log("Aguardando cadastro pelo navegador...\n");

    while (true) {
        try {
            const res = await axios.get(`${SERVIDOR_FLASK}/daemon_poll`, { timeout: 5000 });
            if (res.data?.status === "ok" && res.data.session_id) {
                await processarSessao(res.data.session_id);
                // Após finalizar, volta a aguardar nova sessão
                console.log("\n⏳ Aguardando próxima sessão...\n");
                base64Referencia = null; // limpa âncora para a próxima sessão
            }
        } catch (e) {
            // Servidor offline ou sem resposta — silencioso
        }
        await new Promise(r => setTimeout(r, POLL_INTERVAL));
    }
}

daemonLoop();