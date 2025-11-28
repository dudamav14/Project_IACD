# Project_IACD
API: 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
INSTRUÇÕES DE EXECUÇÃO - PROJETO WISEIN

1. Requisitos:
   - Python 3.10 ou superior instalado.

2. Instalação:
   Abra o terminal na pasta deste projeto e execute:
   pip install -r requirements.txt

3. Execução (Interface Visual - Recomendado):
   Execute o comando:
   streamlit run app_ui.py

4. Logs de Execução:
   Durante o uso da interface web, verifique a janela do terminal/CMD.
   O sistema imprimirá logs detalhados (com a tag [BACKEND LOG]) mostrando:
   - Status da conexão com a API.
   - Passos explorados pelo algoritmo CSP.
   - Nós visitados pelo algoritmo Minimax.

5. Notas sobre a API:
   O projeto utiliza uma chave gratuita do OpenRouter. Se houver falha na conexão (Erro 429),
   o sistema ativará automaticamente o modo 'Failover', garantindo que os algoritmos locais
   continuam a funcionar.