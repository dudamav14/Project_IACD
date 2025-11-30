import asyncio
import sys
import time
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from googlesearch import search
from typing import List, Dict, Optional

try:
    try:
        from logic.csp_quiz import QuizCSP
        from logic.adversarial import InterviewGame
        from logic.metrics import MetricsLogger
    except ImportError:
        from logic.csp_quiz import QuizCSP
        from logic.adversarial import InterviewGame
        from logic.metrics import MetricsLogger

    metrics_logger = MetricsLogger()
    print("[SYSTEM] Módulos de Lógica (CSP/Adversarial) carregados.")
except ImportError as e:
    print(f"[ERRO CRÍTICO] Não foi possível carregar a lógica: {e}")
    sys.exit(1)

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


QUESTION_POOL = [
    {'id': 101, 'topic': 'python', 'level': 'easy', 'type': 'multiple_choice', 'category': 'vocab'},
    {'id': 102, 'topic': 'python', 'level': 'medium', 'type': 'multiple_choice', 'category': 'vocab'},
    {'id': 103, 'topic': 'python', 'level': 'hard', 'type': 'multiple_choice', 'category': 'vocab'},
    {'id': 104, 'topic': 'python', 'level': 'medium', 'type': 'true_false', 'category': 'vocab'},
    {'id': 105, 'topic': 'python', 'level': 'hard', 'type': 'code_completion', 'category': 'grammar'},
    {'id': 201, 'topic': 'AWS', 'level': 'hard', 'type': 'multiple_choice', 'category': 'vocab'},
]



async def generate_quiz_plan(topic: str) -> str:
    """Ferramenta CSP: Gera um plano de estudo otimizado."""
    print(f"\n[TOOL USAGE] Agente a invocar CSP para tópico: {topic}...")
    
    search_topic = 'python' if 'python' in topic.lower() else 'AWS'
    constraints = {'size': 3, 'topic': search_topic, 'max_mc': 2, 'min_grammar': 0}
    if search_topic == 'python': constraints['min_grammar'] = 1

    solver = QuizCSP(QUESTION_POOL, constraints)
    quiz, stats = solver.solve()

    if metrics_logger:
        metrics_logger.log_csp_efficiency(stats.get('time_seconds', 0), stats.get('steps_explored', 0))

    if stats.get("success") and quiz:
        q_list = ", ".join([f"Q{q['id']}({q['type']})" for q in quiz])
        return f"SUCESSO CSP: Quiz gerado: [{q_list}]. Eficiência: {stats['steps_explored']} passos."
    return "FALHA CSP: Restrições impossíveis para o pool atual."

async def next_adversarial_move(last_answer: str) -> str:
    """Ferramenta Adversarial: Escolhe a próxima pergunta."""
    print(f"\n[TOOL USAGE] Agente a invocar Minimax (Adversarial Search)...")
    
    game = InterviewGame(QUESTION_POOL, [101]) # Simula histórico
    best_q, stats = game.get_best_next_question()

    if best_q:
        if metrics_logger:
            metrics_logger.log_adversarial_decision(stats['time_seconds'], stats['nodes_visited'])
        return f"SUCESSO MINIMAX: Próxima pergunta sugerida: ID {best_q['id']} (Nível: {best_q['level']}). Análise: {stats['nodes_visited']} nós."
    return "FALHA MINIMAX: Sem perguntas."

async def search_news(query: str) -> str:
    """Ferramenta RAG Simples."""
    try:
        res = list(search(query, num_results=2, lang="en"))
        return f"LINKS ENCONTRADOS: {res}"
    except:
        return "FALHA NA BUSCA: API Google indisponível."

async def run_wisein_demo(user_input: str):
    print(f"\n{'='*60}")
    print(f" WISEIN SYSTEM | Input: '{user_input}'")
    print(f"{'='*60}\n")

    client = OpenAIChatCompletionClient(**CLIENT_CONFIG)

    assessor = AssistantAgent(
        name="Assessor", model_client=client, tools=[generate_quiz_plan],
        system_message="Tu és o Assessor. Usa 'generate_quiz_plan'."
    )
    tutor = AssistantAgent(
        name="Tutor", model_client=client, tools=[next_adversarial_move],
        system_message="Tu és o Tutor. Usa 'next_adversarial_move'."
    )
    curator = AssistantAgent(
        name="Curador", model_client=client, tools=[search_news],
        system_message="Tu és o Curador. Usa 'search_news'."
    )

    active_agent = tutor 
    tool_to_force = None

    if "quiz" in user_input.lower() or "plano" in user_input.lower():
        print(">> ROUTER: Redirecionando para o Agente ASSESSOR (CSP)...")
        active_agent = assessor
        tool_to_force = generate_quiz_plan
    
    elif "entrevista" in user_input.lower() or "pergunta" in user_input.lower():
        print(">> ROUTER: Redirecionando para o Agente TUTOR (Adversarial)...")
        active_agent = tutor
        tool_to_force = next_adversarial_move
    
    elif "notícia" in user_input.lower():
        print(">> ROUTER: Redirecionando para o Agente CURADOR (RAG)...")
        active_agent = curator
        tool_to_force = search_news

    try:
        result = await active_agent.run(task=user_input)
        print("\n" + "-"*30)
        print(f"RESPOSTA DO AGENTE ({active_agent.name}):")
        print("-" * 30)
        print(result.messages[-1].content)
        print("-" * 30)

    except Exception as e:
        print(f"\nAVISO: A API LLM falhou ({str(e)}).")
        print("ATIVANDO MODO DE FAILOVER (Execução Local dos Algoritmos)...")
        
        if tool_to_force:
            print(f"\n[SISTEMA] Executando a ferramenta '{tool_to_force.__name__}' manualmente para demonstrar a lógica...")
            if tool_to_force == generate_quiz_plan:
                resultado = await generate_quiz_plan(user_input)
            elif tool_to_force == next_adversarial_move:
                resultado = await next_adversarial_move("Start Interview")
            else:
                resultado = await search_news(user_input)
            
            print("\n" + "*"*30)
            print("RESULTADO DO ALGORITMO (FAILOVER):")
            print("*" * 30)
            print(resultado)
            print("*" * 30)
        else:
            print("Não foi possível determinar qual ferramenta executar.")

    await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(run_wisein_demo("Quero um plano de quiz sobre Python"))
    except Exception as e:
        print(f"Erro no Teste 1: {e}")

    print("\n--------------------------------------------------")
    print("Aguardando 5 segundos para recuperar a API...")
    print("--------------------------------------------------\n")
    time.sleep(5) 

    
    try:
        asyncio.run(run_wisein_demo("Estou pronto para a entrevista"))
    except Exception as e:
        print(f"Erro no Teste 2: {e}")
    