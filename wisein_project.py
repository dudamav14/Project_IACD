import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.conditions import TextMentionTermination
from googlesearch import search
from typing import List, Dict, Optional

try:
    from Project_IACD.logic.csp_quiz import QuizCSP
    from Project_IACD.logic.adversarial import InterviewGame
    from Project_IACD.logic.metrics import MetricsLogger

    metrics_logger = MetricsLogger()  # Inicializa o Logger para o relatório
    print("[SUCESSO] Algoritmos importados com sucesso.")
except ImportError:
    # Fallback para evitar que o programa crashe se o ficheiro não estiver lá
    print("\n[ERRO FATAL] Falha na importação dos Algoritmos. A usar Mocks.")


    class QuizCSP:
        def __init__(self, *args): pass

        def solve(self): return None, {"success": False}  # Retorna estrutura mínima de falha


    class InterviewGame:
        def __init__(self, *args): pass

        def get_best_next_question(self): return {"id": "MOCK_AS_ID", "level": "hard"}


    metrics_logger = None

#CONFIGURAÇÃO DE ACESSO E MODELO

#Chave inserida diretamente no código (mudar isto eventualmente)
OPENROUTER_API_KEY = "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"

CLIENT_CONFIG = {
    "model": "meta-llama/llama-3.3-70b-instruct:free",
    "api_key": OPENROUTER_API_KEY,
    "base_url": "https://openrouter.ai/api/v1",
    "model_info": {"vision": False, "function_calling": True, "json_output": False, "family": "unknown",
                   "structured_output": True}
}
BASE_AGENT_PARAMS = {"model_client_stream": False, "reflect_on_tool_use": False}

#RECURSOS PARTILHADOS (POOL DE PERGUNTAS)
#POOL USADO PELOS WRAPPERS DE CSP E AS.
QUESTION_POOL = [
    {'id': 101, 'topic': 'python', 'level': 'easy', 'type': 'multiple_choice', 'category': 'vocab'},
    {'id': 105, 'topic': 'python', 'level': 'hard', 'type': 'code_completion', 'category': 'grammar'},
    {'id': 201, 'topic': 'AWS', 'level': 'medium', 'type': 'true_false', 'category': 'vocab'},
    {'id': 202, 'topic': 'AWS', 'level': 'hard', 'type': 'multiple_choice', 'category': 'vocab'},
    {'id': 301, 'topic': 'docker', 'level': 'easy', 'type': 'multiple_choice', 'category': 'vocab'}
]


#WRAPPER TOOLS (Ligação com as Classes da parte lógica)

def generate_quiz_plan(constraints_str: str) -> str:
    """WRAPPER: Chama a lógica de Backtracking do CSP."""
    #Definir Restrições de Teste (pode vir do input do LLM)
    constraints = {'size': 3, 'topic': 'python', 'max_mc': 1, 'min_grammar': 1}

    #Executar o CSP
    solver = QuizCSP(QUESTION_POOL, constraints)
    quiz_questions, stats = solver.solve()

    #Performance para o Relatório
    if metrics_logger:
        metrics_logger.log_csp_efficiency(stats.get('time_seconds', 0), stats.get('steps_explored', 0))

    if stats.get("success"):
        topic_list = [f"ID {q['id']} ({q['type']})" for q in quiz_questions]
        return f"SUCCESS: Plano de Quiz CSP gerado. IDs: {topic_list}. O Backtracking demorou {stats.get('steps_explored', 0)} passos."
    return "FAILURE: Impossível gerar quiz com as restrições de teste."


def next_adversarial_move(history_str: str) -> str:
    """WRAPPER: Chama o Minimax para escolher a próxima pergunta desafiadora."""
    history_ids = [101]  # Assume que o aluno respondeu à primeira pergunta
    game = InterviewGame(QUESTION_POOL, history_ids)
    best_question = game.get_best_next_question()  # Executa o Minimax

    if best_question and best_question.get('id') != "MOCK_AS_ID":
        #TODO: Uncomment nesta linha depois de implementar 'log_adversarial_decision'
        # no ficheiro metrics.py, para o Relatório de Métricas
        #metrics_logger.log_adversarial_decision(best_question.get('level'))
        return f"SUCCESS: Pergunta ótima (Minimax) escolhida: ID {best_question.get('id')}, Nível {best_question.get('level')}."
    return "FAILURE: Nenhuma pergunta disponível."


def search_tech_news(query: str, num_results: int = 3) -> str:
    """Ferramenta Externa: Procura conteúdo técnico (Tool do Curador)."""
    try:
        results = list(search(query + " technical news", num_results=num_results, lang="en"))
        if results:
            return "SUCCESS: Links encontrados: " + " | ".join(results)
        return "FAILURE: Nenhuma notícia relevante encontrada."
    except Exception as e:
        return f"ERROR: Falha na pesquisa. {str(e)}"


#ARQUITETURA DE AGENTES (WISEIN)

async def run_wisein_project_test(user_input: str):
    client = OpenAIChatCompletionClient(**CLIENT_CONFIG)

    #COORDENADOR (Workflow Manager)
    coordinator = AssistantAgent(
        name="Coordinator", **BASE_AGENT_PARAMS, model_client=client,
        system_message="Role: Coordinator. Direciona o pedido do utilizador. Fluxo: Quiz/Avaliação -> Assessor; Tutoria/Simulação -> Tutor; Notícias -> Curador. Responde em Português de Portugal. Usa termos técnicos em Inglês."
    )

    #AVALIADOR (Integração do CSP)
    assessor = AssistantAgent(
        name="Assessor", **BASE_AGENT_PARAMS, model_client=client,
        tools=[generate_quiz_plan],
        system_message="Role: Assessor. Gere a estrutura do quiz. Invoca a Tool CSP para satisfazer as restrições. Após obter o plano, passa ao Tutor."
    )

    #TUTOR (Integração do AS)
    tutor = AssistantAgent(
        name="Tutor", **BASE_AGENT_PARAMS, model_client=client,
        tools=[next_adversarial_move],
        system_message="Role: Tutor. Interage com o aluno. Usa a Tool AS para simular entrevistas desafiadoras. Termina com FINAL_RESPONSE."
    )

    #CURADOR (Tools Externas)
    curator = AssistantAgent(
        name="Curador", **BASE_AGENT_PARAMS, model_client=client,
        tools=[search_tech_news],
        system_message="Role: Curador. Encontra informação atualizada (Tool Use) e resume para o Tutor. Responde com o resultado da procura."
    )

    #Coordenação (Round Robin para demonstração) --- eventualmente mudar para SelectorGroupChat
    #quando tivermos testes de volume (comprar 1000 requests?)
    team = RoundRobinGroupChat(
        [coordinator, assessor, tutor, curator],
        max_turns=15,
        termination_condition=TextMentionTermination("FINAL_RESPONSE")
    )

    print("\n--- TESTE DE INTEGRAÇÃO DO PROJETO WISEIN ---")
    await Console(team.run_stream(task=user_input))

    await client.close()


if __name__ == "__main__":
    #Teste: O Coordenador deve direcionar a mensagem ao Assessor (CSP)
    asyncio.run(run_wisein_project_test("Quero um quiz focado em vocabulário AWS."))