import streamlit as st
import asyncio
import time
import os
import sys
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from googlesearch import search

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL
# ==============================================================================
st.set_page_config(page_title="WiseIn", page_icon="logo.png", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 3rem; padding-bottom: 5rem; max_width: 900px; }
    .stChatMessage { background-color: transparent; border: none; }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) { background-color: #F0F6F9; border-radius: 15px; padding: 15px; margin-bottom: 15px; }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 15px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
    .stChatInputContainer { padding-bottom: 20px; padding-top: 10px; background-color: white; }
    .stChatInput textarea { background-color: #F8F9FA; border: 1px solid #D1D5DB; border-radius: 25px; font-size: 16px; }
    h1, h2, h3 { color: #205474; font-family: 'Helvetica', sans-serif; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. IMPORTAÇÃO SEGURA & LOGGING
# ==============================================================================
def log_to_terminal(message):
    """Força a escrita no CMD para o professor ver."""
    print(f"\n[BACKEND LOG] {message}")
    sys.stdout.flush()

try:
    try:
        from logic.csp_quiz import QuizCSP
        from logic.adversarial import InterviewGame
        from logic.metrics import MetricsLogger
    except ImportError:
        from logic.csp_quiz import QuizCSP
        from logic.adversarial import InterviewGame
        from logic.metrics import MetricsLogger
    
    log_to_terminal("Módulos de Lógica (CSP/Adversarial) carregados com sucesso.")
    metrics_logger = MetricsLogger()
except ImportError:
    st.error("Erro: Pasta de lógica não encontrada.")
    st.stop()

# ==============================================================================
# 3. CONFIGURAÇÃO API & DADOS
# ==============================================================================
OPENROUTER_API_KEY = "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"

CLIENT_CONFIG = {
    "model": "meta-llama/llama-3-8b-instruct:free",
    "api_key": OPENROUTER_API_KEY,
    "base_url": "https://openrouter.ai/api/v1",
    "model_info": {"vision": False, "function_calling": True, "json_output": False, "family": "llama3", "structured_output": True}
}

MOCK_KNOWLEDGE_BASE = {
    101: {"q": "Qual keyword define uma função em Python?", "a": "def", "ok": " **Correto!** `def` inicia funções.", "nok": " **Errado.** É `def`."},
    102: {"q": "Listas são mutáveis ou imutáveis?", "a": "mutáveis", "ok": " **Certo!** Listas mudam.", "nok": " **Errado.** Elas são mutáveis."},
    103: {"q": "O que é o GIL?", "a": "global interpreter lock", "ok": " **Exato!**", "nok": " Global Interpreter Lock."},
    104: {"q": "Python é compilado estaticamente? (Sim/Não)", "a": "não", "ok": " **Certo**, é dinâmico.", "nok": " **Errado**."},
    105: {"q": "Complete: `___ : try code` ... `except:`", "a": "try", "ok": " **Perfeito**.", "nok": " É `try`."},
    201: {"q": "Serviço Serverless da AWS?", "a": "lambda", "ok": " **Correto**.", "nok": " É o Lambda."}
}

QUESTION_POOL = [
    {'id': 101, 'topic': 'python', 'level': 'easy', 'type': 'multiple_choice', 'category': 'vocab'},
    {'id': 102, 'topic': 'python', 'level': 'medium', 'type': 'multiple_choice', 'category': 'vocab'},
    {'id': 103, 'topic': 'python', 'level': 'hard', 'type': 'multiple_choice', 'category': 'vocab'},
    {'id': 104, 'topic': 'python', 'level': 'medium', 'type': 'true_false', 'category': 'vocab'},
    {'id': 105, 'topic': 'python', 'level': 'hard', 'type': 'code_completion', 'category': 'grammar'},
    {'id': 201, 'topic': 'AWS', 'level': 'hard', 'type': 'multiple_choice', 'category': 'vocab'},
]

# ==============================================================================
# 4. FUNÇÕES LÓGICAS (WRAPPERS COM LOGS)
# ==============================================================================

async def generate_quiz_plan(topic: str) -> str:
    log_to_terminal(f"Iniciando Algoritmo CSP para tópico: '{topic}'")
    
    search_topic = 'python' if 'python' in topic.lower() else 'AWS'
    constraints = {'size': 3, 'topic': search_topic, 'max_mc': 2, 'min_grammar': 0}
    if search_topic == 'python': constraints['min_grammar'] = 1

    solver = QuizCSP(QUESTION_POOL, constraints)
    quiz, stats = solver.solve()
    
    if quiz:
        log_to_terminal(f"CSP Sucesso! Passos: {stats['steps_explored']} | Tempo: {stats['time_seconds']:.6f}s")
        return {"success": True, "data": quiz, "stats": stats, "type": "quiz_plan"}
    
    log_to_terminal("CSP Falhou: Restrições impossíveis.")
    return {"success": False, "msg": "Restrições impossíveis."}

async def next_adversarial_move(ctx: str) -> str:
    log_to_terminal("Iniciando Algoritmo Minimax (Adversarial Search)...")
    
    game = InterviewGame(QUESTION_POOL, [101]) 
    best_q, stats = game.get_best_next_question()
    
    if best_q:
        log_to_terminal(f"Minimax Sucesso! Nós visitados: {stats['nodes_visited']} | Decisão: ID {best_q['id']}")
        return {"success": True, "data": [best_q], "stats": stats, "type": "interview_step"}
    
    log_to_terminal("Minimax Falhou: Sem perguntas.")
    return {"success": False}

# ==============================================================================
# 5. ROUTER HÍBRIDO
# ==============================================================================

async def agent_router(user_input):
    log_to_terminal(f"Recebido Input do Usuário: '{user_input}'")
    client = OpenAIChatCompletionClient(**CLIENT_CONFIG)
    
    router_agent = AssistantAgent(
        name="WiseIn",
        model_client=client,
        system_message="Você é o WiseIn. Se o usuário pedir 'Quiz', 'Entrevista' ou 'Notícias', confirme a ação em uma frase curta."
    )

    api_response = None
    failover_mode = False

    # 1. TENTA A API
    try:
        log_to_terminal("Tentando contactar API LLM (Llama 3)...")
        result = await router_agent.run(task=user_input)
        api_response = result.messages[-1].content
        log_to_terminal("Resposta da API recebida com sucesso.")
    except Exception as e:
        log_to_terminal(f"ALERTA: API Falhou ({str(e)}). Ativando Failover Local.")
        failover_mode = True 
    
    # 2. EXECUTA A LÓGICA
    tool_result = None
    if "quiz" in user_input.lower():
        tool_result = await generate_quiz_plan(user_input)
    elif "entrevista" in user_input.lower():
        tool_result = await next_adversarial_move(user_input)
    
    return api_response, tool_result, failover_mode

# ==============================================================================
# 6. UI
# ==============================================================================

def main():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.title("WISEIN")

    with st.sidebar:
        st.caption("Painel de Controle")
        st.success("Sistema Online")
        st.markdown("---")
        if st.button("Reiniciar Sessão", type="primary", use_container_width=True):
            st.session_state.messages = []
            st.session_state.active_session = None
            st.session_state.q_queue = []
            st.session_state.q_index = 0
            st.rerun()
        st.markdown("---")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Olá! Sou o seu tutor técnico **WiseIn**. \n\nPosso gerar um plano de estudos personalizado ou simular uma entrevista técnica. Como quer começar?"}]
    if "active_session" not in st.session_state:
        st.session_state.active_session = None 
    if "q_queue" not in st.session_state:
        st.session_state.q_queue = []
    if "q_index" not in st.session_state:
        st.session_state.q_index = 0

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Escreva aqui (ex: 'Quero um quiz de Python')..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            if st.session_state.active_session:
                current_q = st.session_state.q_queue[st.session_state.q_index]
                db_data = MOCK_KNOWLEDGE_BASE.get(current_q['id'])
                
                if db_data:
                    log_to_terminal(f"Processando resposta do utilizador para Q{current_q['id']}...")
                    correct = prompt.lower() in db_data['a'].lower()
                    feedback = db_data['ok'] if correct else db_data['nok']
                    
                    final_txt = f"{feedback}"
                    st.session_state.q_index += 1
                    
                    if st.session_state.q_index < len(st.session_state.q_queue):
                        next_q = st.session_state.q_queue[st.session_state.q_index]
                        next_db = MOCK_KNOWLEDGE_BASE.get(next_q['id'])
                        if next_db:
                            final_txt += f"\n\n---\n**Próxima Pergunta:** {next_db['q']}"
                    else:
                        final_txt += "\n\n **Parabéns! Sessão concluída.**"
                        st.session_state.active_session = None
                        log_to_terminal("Sessão de Quiz concluída.")
                    
                    response_placeholder.markdown(final_txt)
                    st.session_state.messages.append({"role": "assistant", "content": final_txt})
                else:
                    st.error("Erro interno.")

            else:
                with st.spinner("Processando..."):
                    api_text, logic_result, failover = asyncio.run(agent_router(prompt))
                
                display_text = ""
                
                if not failover and api_text:
                    display_text += f"{api_text}\n\n"
                elif failover:
                    display_text += f"⚙️ *Modo Offline Ativado.*\n\n"

                if logic_result and logic_result['success']:
                    st.session_state.q_queue = logic_result['data']
                    st.session_state.active_session = 'quiz'
                    st.session_state.q_index = 0
                    
                    first_id = logic_result['data'][0]['id']
                    first_db = MOCK_KNOWLEDGE_BASE.get(first_id)
                    stats = logic_result['stats']
                    
                    if first_db:
                        display_text += f"**Plano Gerado com Sucesso**\n"
                        display_text += f"_Análise concluída em {stats['time_seconds']:.4f}s._\n\n"
                        display_text += f"---\n**Pergunta 1:** {first_db['q']}"
                    
                else:
                    display_text += "Não consegui gerar um plano para esse tópico. Tente 'Python' ou 'AWS'."

                response_placeholder.markdown(display_text)
                st.session_state.messages.append({"role": "assistant", "content": display_text})

if __name__ == "__main__":
    main()