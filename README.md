WiseIn
Sistema Multi-Agente para Avaliação de Competência Técnica

Este projeto implementa um sistema de tutoria inteligente que utiliza uma arquitetura multi-agente (Router, Assessor, Tutor, Curador) para gerar planos de estudo (via algoritmo CSP) e simular entrevistas técnicas (via algoritmo Minimax).

1. Pré-requisitos
Python 3.10 ou superior instalado.
Conexão à Internet (para o funcionamento dos Agentes LLM).

2. Instalação
Abra o terminal/CMD na pasta raiz deste projeto.
Instale as dependências necessárias executando:

pip install -r requirements.txt

3. Configuração da API Key (Importante)
O projeto requer uma chave de API do OpenRouter para ativar a inteligência dos agentes. **Use nossa chave!** nosso projeto requer um volume alto de requests e a chave gratuita não é suficiente para isso.

1-Abra o arquivo app_ui.py num editor de texto ou IDE.

2-Procure pela variável OPENROUTER_API_KEY (localizada na linha 56).

3-Substitua o valor existente pela chave fornecida: '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'

4-Salve o arquivo.

4. Execução (Interface Visual)
Para iniciar a aplicação web, execute no terminal:

streamlit run app_ui.py
O navegador abrirá automaticamente com a interface do WiseIn.

5. Monitorização e Logs
Durante a utilização da interface web, mantenha o terminal aberto para visualizar os Logs de Backend. O sistema imprime informações técnicas em tempo real:

[BACKEND LOG] Status da conexão com a API e Router.

[METRIC - CSP] Eficiência e passos explorados na geração do Quiz.

[METRIC - ADVERSARIAL] Nós visitados pelo algoritmo Minimax na Entrevista.

6. Notas sobre Failover
O sistema possui um mecanismo de Failover Automático. Caso a API do OpenRouter falhe (ex: Erro 429 - Rate Limit ou falta de créditos), o sistema não irá falhar. Ele ativará automaticamente o Modo Offline, executando os algoritmos CSP e Minimax localmente com base numa Base de Conhecimento interna, garantindo que a demonstração funcional nunca é interrompida.