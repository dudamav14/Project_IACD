# Logic(Módulo de Raciocínio)

Este diretório contém a implementação dos algoritmos de **Problem Solving** requeridos no projeto.
Aqui reside o "cérebro" não-agêntico que toma decisões otimizadas (CSP) e estratégicas (Adversarial Search).

## Estado Atual
- **CSP (Gerador de Quiz):**Implementado (Backtracking com poda). Suporta restrições de variedade e competência.
- **Adversarial Search (Entrevistador):**Implementado (Minimax com profundidade 2).
- **Métricas:**Integradas (O CSP retorna estatísticas de tempo e passos para o relatório).
- **Testes:**`test_logic.py` valida a integração (apenas para dev, não usar em produção).

---

## Contrato de Dados (Importante para o RAG)
Para que estes algoritmos funcionem, as perguntas que vêm do teu Agente de Curadoria/RAG DEVEM ser convertidas para dicionários com as seguintes chaves:

| Chave      | Tipo      | Valores Esperados                       | Uso                              |
| :---       | :---      | :---                                    | :---                             |
| `id`       | `int/str` | Único                                   | Identificação e Histórico.       |
| `topic`    | `str`     | 'python', 'docker'...                   | Filtragem do CSP.                |
| `level`    | `str`     | 'easy', 'medium', 'hard'                | Cálculo de utilidade do Minimax. |
| `type`     | `str`     | 'multiple_choice', 'code', 'true_false' | Restrição de Variedade.          |
| `category` | `str`     | 'vocab', 'grammar', 'reading'           | Restrição de Competência.        |

> **Nota:** O código possui tratamento defensivo (`.get()`), mas a qualidade da decisão depende destes dados.

---

## Como Usar nos Agentes (Instruções para o Tomé)
 
### 1. Gerar um Quiz Otimizado (Agente de Avaliação)
Use a classe `QuizCSP` quando o usuário pedir um teste.

``` 
python
from logic_core.csp_quiz import QuizCSP

# 1. Receba a lista bruta do seu RAG
raw_questions = tool_rag_search("python") 

# 2. Defina as restrições (Pode vir do prompt do usuário ou ser fixo)
constraints = {
    'size': 5,             # Tamanho do quiz
    'topic': 'python',     # Tópico obrigatório
    'max_mc': 3,           # Máx. de múltipla escolha (Variedade)
    'min_grammar': 1       # Mín. de gramática (Equilíbrio)
}

# 3. Execute o Solver
solver = QuizCSP(raw_questions, constraints)
quiz_questions, stats = solver.solve()

# 4. Use o resultado
if quiz_questions:
    # stats contém {'time_seconds': 0.001, 'steps_explored': 45, ...}
    # Útil para mostrar no relatório ou logar eficiência!
    return quiz_questions
else:
    return "Não foi possível gerar um quiz válido com essas restrições."

```

 
