# Relatório de Construção do Sistema: Storytelling Interativo com IA

## 1. Introdução

**Qual é o problema?**
O ensino tradicional de fatos históricos e conceitos complexos (como computação ou exploração espacial) muitas vezes esbarra na falta de engajamento dos alunos. A absorção de conteúdo de forma passiva não captura a atenção prolongada, especialmente do público infantil, que demanda estímulos visuais e interativos.

**Por que storytelling infantil?**
As crianças aprendem melhor através de narrativas imersivas e exemplos lúdicos. O storytelling permite transformar figuras históricas em personagens de uma aventura, fazendo com que a criança se torne o protagonista. Em vez de ler sobre Alan Turing, a criança trabalha ao lado dele.

**Por que IA?**
A Inteligência Artificial resolve o problema da escalabilidade e da personalização. Em vez de histórias estáticas (como um livro-jogo comum onde as opções são limitadas e pré-desenhadas), a IA generativa permite criar diálogos dinâmicos, gerar ilustrações personalizadas na hora (onde o avatar do próprio aluno aparece na cena) e adaptar as reações do ambiente de acordo com cada escolha. 

**Qual é o objetivo?**
Desenvolver um sistema imersivo de contação de histórias interativas que combina processamento de linguagem natural (LLM) para geração de narrativas dinâmicas, geração de imagens/vídeos em tempo real para construção de storyboards, e interação com um robô físico (NAO) para engajamento e TTS (Text-to-Speech).

---

## 2. Referencial Teórico

**Storytelling e Storytelling Interativo**
A arte de contar histórias cria conexões emocionais. No storytelling interativo, a narrativa se ramifica, dando agência ao usuário. Essa interatividade aumenta a retenção de conhecimento.

**IA na Educação**
A utilização de IA na educação possibilita tutores personalizados. No contexto deste projeto, a IA atua como um "Mestre de RPG" e Diretor de Arte simultaneamente.

**LLMs (Large Language Models)**
Modelos como o Llama 3.1 são capazes de seguir instruções precisas (system prompts) para gerar não apenas texto literário, mas saídas estruturadas em formato JSON, fundamentais para a comunicação entre sistemas.

**Geração de Imagens e Consistência (Personalização)**
Ferramentas baseadas em Stable Diffusion geram visuais de alta qualidade. O maior desafio no uso de IA para quadrinhos/storyboards é a consistência visual. Técnicas avançadas, como o uso de **IP-Adapter** (Image Prompt Adapter), permitem usar a primeira imagem gerada de um personagem como referência para manter suas feições idênticas nos quadros subsequentes.

---

## 3. Metodologia (Construção do Sistema)

O sistema foi concebido com uma arquitetura distribuída, dividida entre um servidor de gerenciamento narrativo (Flask/Python), um cliente orquestrador de geração/robótica (Node.js), e APIs de IA generativa (Ollama e SD Forge).

### 3.1. Arquitetura e Modelos Utilizados
*   **LLM (Geração de Texto):** Utilizou-se o modelo **Llama 3.1** rodando localmente via **Ollama**. 
*   **Geração de Imagem:** Utilizou-se a API do **Forge (Stable Diffusion WebUI Forge)** com o modelo no estilo "ToonYou 3D Animation / Pixar" para geração via `txt2img`.
*   **Consistência de Personagem:** A integração do **IP-Adapter** no ControlNet para fixar o rosto e a roupa da criança durante toda a história.
*   **Robótica/TTS:** Comunicação via requisições HTTP com a ponte de um robô educacional **NAO** para narração e interações gestuais.
*   **Vídeo e Fundo:** Utilização da API SVD (Stable Video Diffusion) para animações de quadros e `rembg` (u2net) para remoção de fundos.

### 3.2. Engenharia de Prompts (Prompt Engineering)
A técnica principal para controlar o LLM foi a criação de um **System Prompt Bilíngue e Estruturado**. O Llama foi configurado para atuar como um "Diretor Profissional e Narrador". 
A instrução exigia a saída de um **JSON estrito** com as seguintes regras:
1.  **Narrativa (PT-BR):** Um parágrafo rico, sempre em 3ª pessoa, descrevendo a situação atual.
2.  **Opções (PT-BR):** Duas ações interativas baseadas no evento histórico em andamento.
3.  **Personagens (EN-US):** A descrição física exata de cada personagem em cena (vital para o gerador de imagem). O prompt blinda o visual do aluno para que a IA nunca altere sua roupa, cabelo, cor de pele e olhos escolhidos no início da sessão.
4.  **Microcenas (EN-US):** O LLM é instruído a gerar *exatamente 4 microcenas* (para compor um storyboard). Ele é obrigado a fornecer informações de "ação" dinâmica, "câmera" (close-up, wide shot), "emoção" e "cenário", escrevendo tudo em inglês para evitar *crashes* ao repassar esses metadados diretamente ao gerador de imagens (Stable Diffusion).

### 3.3. Fluxo de Dados e Integração (Fluxo entre as IAs)
1.  **Setup (Node.js):** O usuário inicia a sessão (Ex: jornada Alan Turing). O sistema coleta características físicas do aluno (tipo de cabelo, pele, olhos) para montar uma *tag* visual base.
2.  **State Manager (Flask):** O servidor inicia a árvore narrativa (*Blueprints*) definindo metas, fatos históricos e emoções daquele capítulo (Ex: explicar a Máquina Enigma).
3.  **Geração Textual (Ollama):** O Flask funde o contexto histórico atual + histórico das escolhas passadas + visual do aluno em um prompt. O Llama 3.1 gera o JSON da cena.
4.  **Storyboard e Camadas (Forge):** O `story_client.js` recebe os prompts de imagem. Ele utiliza a API do Forge (`txt2img`) para gerar os quadros em lote. Na geração da primeira imagem do aluno, ela é salva como *referência global*. Nas cenas seguintes, o script injeta essa imagem no `alwayson_scripts` (via ControlNet / IP-Adapter), forçando a IA a manter o mesmo rosto.
5.  **Fala e Animação (NAO):** Enquanto o servidor e a GPU processam pesadamente imagens, o cliente envia comandos de "enrolação" (Ex: "Acessando os arquivos históricos... Preparando nossa viagem.") para o robô NAO falar, mascarando o tempo de carregamento com engajamento.

---

## 4. Resultados e Discussão

O uso de instruções restritas para saída em JSON via Ollama demonstrou ser altamente confiável. A divisão linguística no prompt — forçando o texto da história e opções para o usuário final em Português, e as descrições técnicas de cenário e câmera estritamente em Inglês — reduziu drasticamente os erros de interpretação do Stable Diffusion, eliminando imagens distorcidas causadas por prompts em PT-BR.

A estratégia de fixar o *visual description* no gerenciador de estados (Python) e usar a primeira imagem como âncora do IP-Adapter (Node.js) garantiu uma consistência notável (personagens não mudam de aparência entre as cenas), superando o maior desafio da geração iterativa.
Por fim, o uso de temporizadores dinâmicos no robô mascarou o tempo natural de geração local do LLM e difusão das imagens, mantendo a criança presa à "magia" do momento.

---

## 5. Conclusão

O sistema provou que a orquestração inteligente de diferentes modelos locais e de código aberto (Llama 3.1, SD Forge, Rembg) integrados a hardwares físicos e interfaces gráficas consegue criar experiências educacionais profundas. Ao dar agência às crianças dentro de uma narrativa adaptativa e visualmente gerada sob medida, a plataforma se posiciona como uma ferramenta imersiva inovadora. A técnica de forçar saídas JSON e gerenciar o estado atua como o elo perfeito entre o controle algorítmico tradicional e a criatividade fluida das IAs modernas.
