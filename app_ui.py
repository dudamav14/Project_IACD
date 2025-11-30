import streamlit as st
import asyncio
import json
import time
import os
import sys
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from googlesearch import search

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
    
    .question-box {
        background-color: #E3F2FD;
        border-left: 5px solid #205474;
        padding: 15px;
        border-radius: 5px;
        margin-top: 10px;
        font-weight: 500;
        color: #0D47A1;
    }
    
    .algo-tag {
        font-size: 0.8em;
        background-color: #eee;
        padding: 2px 8px;
        border-radius: 10px;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

def log_to_terminal(message):
    print(f"\n[BACKEND LOG] {message}")
    sys.stdout.flush()

try:
    from logic.csp_quiz import QuizCSP
    from logic.adversarial import InterviewGame
    from logic.metrics import MetricsLogger
    metrics_logger = MetricsLogger()
except ImportError:
    st.error("Erro: Pasta de lógica não encontrada.")
    st.stop()

OPENROUTER_API_KEY = " " # <--- INSERE A CHAVE AQUI

CLIENT_CONFIG = {
    "model": "openai/gpt-4o-mini",
    "api_key": OPENROUTER_API_KEY,
    "base_url": "https://openrouter.ai/api/v1",
    "model_info": {
        "vision": False, 
        "function_calling": True, 
        "json_output": False, 
        "family": "gpt-4", 
        "structured_output": True
    }
}

STATIC_KNOWLEDGE = {
    101: {"q": "Qual keyword define uma função em Python?", "a": "def", "ok": "Correto!", "nok": "Errado. É 'def'."},
    102: {"q": "Listas são mutáveis ou imutáveis?", "a": "mutáveis", "ok": "Certo!", "nok": "Errado."},
    103: {"q": "O que é o GIL?", "a": "global interpreter lock", "ok": "Exato!", "nok": "Global Interpreter Lock."},
    104: {"q": "Python é compilado estaticamente?", "a": "não", "ok": "Certo.", "nok": "Errado."},
    105: {"q": "Complete: `___ : try code` ... `except:`", "a": "try", "ok": "Perfeito.", "nok": "É 'try'."},
    201: {"q": "Serviço Serverless da AWS?", "a": "lambda", "ok": "Correto.", "nok": "É o Lambda."}
}

STATIC_POOL = [
    {'id': 101, 'topic': 'python', 'level': 'easy', 'type': 'multiple_choice', 'category': 'vocab'},
    {'id': 102, 'topic': 'python', 'level': 'medium', 'type': 'multiple_choice', 'category': 'vocab'},
    {'id': 103, 'topic': 'python', 'level': 'hard', 'type': 'multiple_choice', 'category': 'vocab'},
    {'id': 104, 'topic': 'python', 'level': 'medium', 'type': 'true_false', 'category': 'vocab'},
    {'id': 105, 'topic': 'python', 'level': 'hard', 'type': 'code_completion', 'category': 'grammar'},
    {'id': 201, 'topic': 'AWS', 'level': 'hard', 'type': 'multiple_choice', 'category': 'vocab'},
]

if "DB_PERGUNTAS" not in st.session_state:
    st.session_state.DB_PERGUNTAS = STATIC_KNOWLEDGE.copy()
if "POOL_ATUAL" not in st.session_state:
    st.session_state.POOL_ATUAL = STATIC_POOL.copy()


async def fetch_new_questions(topic):
    client = OpenAIChatCompletionClient(**CLIENT_CONFIG)
    log_to_terminal(f"Tentando gerar perguntas novas sobre '{topic}' via IA...")
    
    prompt = f"""
    Create a technical quiz with 5 questions about '{topic}'.
    Return ONLY a raw JSON list. No markdown formatting (no ```json), no intro text.
    
    Structure per item:
    {{
        "id": 900,
        "topic": "{topic}",
        "level": "easy", 
        "type": "multiple_choice",
        "category": "vocab",
        "q": "Question text here?\\na) Option 1\\nb) Option 2",
        "a": "keyword",
        "ok": "Positive feedback",
        "nok": "Negative feedback"
    }}
    Make sure to include 5 distinct items with IDs starting from 900.
    """
    try:
        agent = AssistantAgent(name="Generator", model_client=client)
        result = await agent.run(task=prompt)
        
        content = result.messages[-1].content
        content = content.replace("```json", "").replace("```", "").strip()
        
        start = content.find("[")
        end = content.rfind("]") + 1
        if start != -1 and end != -1:
            content = content[start:end]
            
        data = json.loads(content)
        
        new_pool = []
        for i, item in enumerate(data):
            
            unique_id = int(time.time()) + i 
            
            q_type = item.get('type', 'multiple_choice')
            q_level = item.get('level', 'medium')
            
            new_pool.append({
                'id': unique_id, 
                'topic': topic, 
                'level': q_level, 
                'type': q_type, 
                'category': item.get('category', 'vocab')
            })
            
            st.session_state.DB_PERGUNTAS[unique_id] = {
                'q': item.get('q', 'Erro no texto'), 
                'a': item.get('a', ''), 
                'ok': item.get('ok', 'Correto!'), 
                'nok': item.get('nok', 'Incorreto.')
            }
        
        st.session_state.POOL_ATUAL.extend(new_pool)
        log_to_terminal(f"Sucesso! {len(new_pool)} perguntas de '{topic}' adicionadas.")
        return True
    
    except Exception as e:
        log_to_terminal(f"Erro na geração JSON: {e}")
        return False


async def generate_quiz_plan(topic: str) -> str:

    await fetch_new_questions(topic)
    
    found_topic = False
    for q in st.session_state.POOL_ATUAL:
        if topic.lower() in q['topic'].lower():
            found_topic = True
            break
            
    search_topic = topic if found_topic else 'python'
    
    if search_topic == 'python' and topic.lower() != 'python':
        log_to_terminal(f"Aviso: Tópico '{topic}' não encontrado. A usar backup 'python'.")

    constraints = {
        'size': 3, 
        'topic': search_topic, 
        'max_mc': 3, 
        'min_grammar': 0 
    }
    
    solver = QuizCSP(st.session_state.POOL_ATUAL, constraints)
    quiz, stats = solver.solve()
    
    if quiz: 
        print(f"\n[METRICAS - CSP (BACKTRACKING)]")
        print(f"   ├── Status: Sucesso (Restrições Rígidas)")
        print(f"   ├── Tópico: {search_topic}")
        print(f"   ├── Espaço de Busca Exploradodo: {stats['steps_explored']} passos")
        print(f"   └── Tempo de Computação: {stats['time_seconds']:.6f} segundos")
        print("-" * 50)
        return {"success": True, "data": quiz, "stats": stats, "type": "quiz_plan"}
    
    solver = QuizCSP(st.session_state.POOL_ATUAL, {'size': 1, 'topic': search_topic})
    quiz, stats = solver.solve()
    if quiz: 
        print(f"\n[METRICAS - CSP (BACKTRACKING)]")
        print(f"   ├── Status: Sucesso (Restrições Rígidas)")
        print(f"   ├── Tópico: {search_topic}")
        print(f"   ├── Espaço de Busca Exploradodo: {stats['steps_explored']} passos")
        print(f"   └── Tempo de Computação: {stats['time_seconds']:.6f} segundos")
        print("-" * 50)
        return {"success": True, "data": quiz, "stats": stats, "type": "quiz_plan"}
    
    return {"success": False}

async def next_adversarial_move(topic: str, history: list) -> dict: 
  
    if not history:
        await fetch_new_questions(topic)
    
    full_pool = st.session_state.POOL_ATUAL
    topic_pool = [q for q in full_pool if topic.lower() in q['topic'].lower()]
 
    if not topic_pool:
        topic_pool = [q for q in full_pool if 'python' in q['topic'].lower()]
        log_to_terminal(f"Aviso: Não há perguntas de '{topic}'. Usando backup (Python).")

    game = InterviewGame(topic_pool, history) 
    best_q, stats = game.get_best_next_question()
    
    if best_q: 
        print(f"\n[METRICAS - ADVERSARIAL (MINIMAX)]")
        print(f"   ├── Estratégia: Maximizar Dificuldade vs Performance")
        print(f"   ├── Nós da Árvore Visitados: {stats['nodes_visited']}")
        print(f"   ├── Decisão Ótima ID: {best_q['id']} (Nível: {best_q['level']})")
        print(f"   └── Tempo de Decisão: {stats['time_seconds']:.6f} segundos")
        print("-" * 50)
        return {"success": True, "data": [best_q], "stats": stats, "type": "interview_step"}
    
    return {"success": False}

async def agent_router(user_input):
    log_to_terminal(f"Input: {user_input}")
    
    clean_input = user_input.lower().replace("?", "").replace("!", "").replace(".", "")
    
    stopwords = [
        "quero", "um", "uma", "quiz", "sobre", "de", "do", "da", "em", "para", 
        "plano", "entrevista", "teste", "gerar", "criar", "fazer", "agora", "rápido"
    ]
    words = clean_input.split()
    potential_topics = [w for w in words if w not in stopwords]

    if potential_topics:
        topic = potential_topics[-1] 
    else:
        topic = "General Tech" #Se o user digitar só "Quero um quiz" e mais nada

    if len(topic) > 3: 
        topic = topic.capitalize()
    else:
        topic = topic.upper()

    log_to_terminal(f"Tópico detetado: '{topic}'")
            
    client = OpenAIChatCompletionClient(**CLIENT_CONFIG)
    router_agent = AssistantAgent(name="WiseIn", model_client=client, system_message="Seja breve.")
    
    api_response = None
    try:
        result = await router_agent.run(task=user_input)
        api_response = result.messages[-1].content
    except:
        pass 
    
    tool_result = None
    if "quiz" in user_input.lower() or "plano" in user_input.lower():
        tool_result = await generate_quiz_plan(topic)
    elif "entrevista" in user_input.lower():
        tool_result = await next_adversarial_move(topic, [])
    
    return api_response, tool_result, False, topic


def main():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        else: st.title("WISEIN")

    with st.sidebar:
        st.caption("Painel de Controle")
        st.success("Sistema Online")
        if st.button("Reiniciar", type="primary", use_container_width=True):
            st.session_state.messages = []
            st.session_state.active_session = None
            st.session_state.active_mode = None 
            st.session_state.history_ids = []  
            st.session_state.current_topic = None
            st.rerun()
        st.caption("WiseIn Tech Tutor")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Olá! Posso gerar um **Quiz** ou **Entrevista**. Qual o tópico?"}]
    if "active_session" not in st.session_state: 
        st.session_state.active_session = None 
        st.session_state.active_mode = None
        st.session_state.history_ids = []
        st.session_state.current_topic = "python"
        st.session_state.q_queue = []
        st.session_state.q_index = 0

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): 
            if '<div class="question-box">' in msg["content"]:
                st.markdown(msg["content"], unsafe_allow_html=True)
            else:
                st.markdown(msg["content"])

    if prompt := st.chat_input("Ex: Quero uma entrevista de Java..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            

            if st.session_state.active_session:
                current_q = st.session_state.q_queue[st.session_state.q_index]
                db_data = st.session_state.DB_PERGUNTAS.get(current_q['id'])
                
                if db_data:
                    correct = prompt.lower() in db_data['a'].lower()
                    feedback = db_data['ok'] if correct else f"{db_data['nok']} (Resp: **{db_data['a']}**)"
                    st.markdown(feedback)
                    st.session_state.messages.append({"role": "assistant", "content": feedback})
                    st.session_state.history_ids.append(current_q['id'])
                    
                    should_continue = False
                    next_q_data = None
                    
                    if st.session_state.active_mode == 'quiz':
                        st.session_state.q_index += 1
                        if st.session_state.q_index < len(st.session_state.q_queue):
                            next_q_data = st.session_state.q_queue[st.session_state.q_index]
                            should_continue = True
                            
                    elif st.session_state.active_mode == 'interview':
                        if len(st.session_state.history_ids) < 5: 
                            with st.spinner("Calculando melhor jogada..."):
                                res = asyncio.run(next_adversarial_move(st.session_state.current_topic, st.session_state.history_ids))
                                if res['success']:
                                    next_q_data = res['data'][0] 
                                    st.session_state.q_queue = [next_q_data]
                                    st.session_state.q_index = 0
                                    should_continue = True
                    
                    if should_continue and next_q_data:
                        next_db = st.session_state.DB_PERGUNTAS.get(next_q_data['id'])
                        if next_db:
                            time.sleep(0.5)
                            prefixo = f"Pergunta {len(st.session_state.history_ids) + 1}"
                            q_display = f"""<div class="question-box">{prefixo}: {next_db['q']}</div>"""
                            st.markdown(q_display, unsafe_allow_html=True)
                            st.session_state.messages.append({"role": "assistant", "content": q_display})
                        else:
                            st.error("Erro dados.")
                    else:
                        end_msg = "**Sessão Terminada!**"
                        st.markdown(end_msg)
                        st.session_state.messages.append({"role": "assistant", "content": end_msg})
                        st.session_state.active_session = None
            
            else:
                with st.spinner("A iniciar agentes..."):
                    api_txt, res, fail, topic_detected = asyncio.run(agent_router(prompt))
                
                if res and res['success']:
                    st.session_state.q_queue = res['data']
                    st.session_state.active_session = True
                    st.session_state.current_topic = topic_detected
                    st.session_state.q_index = 0
                    st.session_state.history_ids = []
                    
                    st.session_state.active_mode = 'quiz' if res['type'] == 'quiz_plan' else 'interview'
                    
                    first = res['data'][0]
                    first_txt = st.session_state.DB_PERGUNTAS[first['id']]['q']
                    stats = res['stats']
                    
                    # Intro
                    intro_html = ""
                    if st.session_state.active_mode == 'quiz':
                        intro_html = f"<b>Plano Gerado</b> <span class='algo-tag'>{stats.get('steps_explored',0)} passos</span><br><br>"
                    else:
                        intro_html = f"<b>Entrevista Iniciada</b> <span class='algo-tag'>{stats.get('nodes_visited',0)} nós</span><br><br>"
                    
                    q_display = f"""{intro_html}<div class="question-box">Pergunta 1: {first_txt}</div>"""
                    st.markdown(q_display, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": q_display})
                    
                else:
                    err_msg = "Não consegui iniciar. Tente 'Quiz de Python' ou 'Entrevista AWS'."
                    st.markdown(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})

if __name__ == "__main__":
    main()