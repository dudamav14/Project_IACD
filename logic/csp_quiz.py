# logic_core/csp_quiz.py
import time
from typing import List, Dict, Optional, Any, Tuple

class QuizCSP:
    def __init__(self, question_pool: List[Dict[str, Any]], constraints: Dict[str, Any]):
        """
        :param question_pool: Lista de dicts (o 'Domínio'). 
                              Ex: [{'id': 1, 'topic': 'Docker', 'difficulty': 'Hard', 'type': 'mc', 'category': 'vocab'}, ...]
        :param constraints: Dict com regras. 
                            Ex: {'size': 5, 'min_hard': 1, 'max_mc': 3, 'min_grammar': 1}
        """
        self.pool = question_pool
        self.constraints = constraints
        self.solution = []

    def is_valid(self, candidate_question):
        """
        O GUARDA DE TRÂNSITO: Verifica se adicionar a 'candidate_question'
        viola alguma regra IMPEDITIVA (Limites Máximos ou Filtros).
        """
        
        # 1. Regra de Duplicidade: Não pode ter a mesma pergunta duas vezes
        if candidate_question in self.solution:
            return False

        # 2. Regra de Tópico: A pergunta tem que ser do tópico pedido
        if 'topic' in self.constraints:
            if candidate_question.get('topic') != self.constraints['topic']:
                return False

        # 3. Regra de Tamanho: Não podemos exceder o tamanho máximo do quiz
        # Simulamos a adição para ver se estoura
        if len(self.solution) >= self.constraints.get('size', 5):
            return False
        
        # --- CONSTRAINT 2: VARIEDADE DE FORMATOS (Máximo de Múltipla Escolha) ---
        # Se a candidata é 'multiple_choice', verificamos se já atingimos o limite
        if 'max_mc' in self.constraints and candidate_question.get('type') == 'multiple_choice':
            count_mc = sum(1 for q in self.solution if q.get('type') == 'multiple_choice')
            if count_mc >= self.constraints['max_mc']:
                return False

        return True

    def check_final_goal(self):
        """
        O JUIZ FINAL: Verifica se a solução completa atende aos requisitos MÍNIMOS.
        Isso roda APENAS quando já selecionamos o número alvo de perguntas.
        """
        
        # Verifica Mínimo de Perguntas Difíceis
        count_hard = sum(1 for q in self.solution if q.get('level') == 'hard')
        min_hard = self.constraints.get('min_hard', 0)
        if count_hard < min_hard:
            return False

        # --- CONSTRAINT 4: EQUILÍBRIO DE COMPETÊNCIAS (Mínimo de Gramática) ---
        if 'min_grammar' in self.constraints:
            count_grammar = sum(1 for q in self.solution if q.get('category') == 'grammar')
            if count_grammar < self.constraints['min_grammar']:
                return False
        
        return True
    
    def solve(self)-> Tuple[Optional[List[Dict]], Dict[str, Any]]:
        """
        Retorna uma tupla: (solucao, metadados)
        """
        start_time = time.time()
        self.steps_count = 0  # Contador de passos para o relatório
        
        result = self._backtracking_search() # Vamos mover a lógica para uma função interna
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        stats = {
            "success": result is not None,
            "time_seconds": execution_time,
            "steps_explored": self.steps_count,
            "quiz_size": len(result) if result else 0
        }
        return result, stats
    
    def _backtracking_search(self):
        """
        O ALGORITMO (Backtracking): Tenta preencher as vagas uma por uma.
        """
        self.steps_count += 1 # Conta cada tentativa
        # CASO BASE: Se o quiz já tem o tamanho desejado
        target_size = self.constraints.get('size', 5)
        
        if len(self.solution) == target_size:
            # O quiz está cheio, agora chamamos o "Juiz Final" para ver se cumpriu as metas mínimas
            if self.check_final_goal():
                return self.solution # SUCESSO!
            else:
                return None # Falha: Tamanho ok, mas faltou algo (ex: faltou gramática).

        # PASSO RECURSIVO: Tentar adicionar perguntas
        for question in self.pool:
            # Posso adicionar esta pergunta? (Respeita os limites máximos?)
            if self.is_valid(question):
                
                # AÇÃO: Adiciona a pergunta
                self.solution.append(question)
                
                # RECURSÃO: Tenta achar a próxima
                result = self.solve()
                
                # Se achou uma solução completa lá na frente, retorna ela
                if result is not None:
                    return result
                
                # BACKTRACK: Se chegou aqui, deu errado lá na frente. Remove e tenta a próxima.
                self.solution.pop()

        # Se testou todas e nada deu certo
        return None

# Para testar sozinho (MOCK):
if __name__ == "__main__":
    # Crie dados falsos com os campos 'type' e 'category' necessários para o teste
    mock_pool = [
        # Perguntas de Python (Várias de múltipla escolha/vocabulário)
        {'id': 1, 'topic': 'python', 'level': 'easy', 'type': 'multiple_choice', 'category': 'vocab'},
        {'id': 2, 'topic': 'python', 'level': 'hard', 'type': 'multiple_choice', 'category': 'vocab'},
        {'id': 3, 'topic': 'python', 'level': 'medium', 'type': 'multiple_choice', 'category': 'vocab'},
        {'id': 4, 'topic': 'python', 'level': 'hard', 'type': 'multiple_choice', 'category': 'vocab'},
        
        # Pergunta de Python diferente (Gramática e formato 'code') - ESSENCIAL PARA FUNCIONAR
        {'id': 5, 'topic': 'python', 'level': 'medium', 'type': 'code_completion', 'category': 'grammar'},
        
        # Outros tópicos (devem ser ignorados)
        {'id': 6, 'topic': 'java', 'level': 'easy', 'type': 'multiple_choice', 'category': 'vocab'},
    ]
    
    # REGRAS: 
    # Quero 3 perguntas de Python.
    # No máximo 2 podem ser múltipla escolha (obriga a pegar a de 'code_completion')
    # Pelo menos 1 tem que ser 'grammar' (obriga a pegar a id 5)
    regras = {
        'size': 3, 
        'topic': 'python', 
        'max_mc': 2, 
        'min_grammar': 1
    }
    
    solver = QuizCSP(mock_pool, regras)
    resultado = solver.solve()
    
    if resultado:
        print("Solução Encontrada:")
        for q in resultado:
            print(f"ID: {q['id']} | Tipo: {q['type']} | Categoria: {q['category']}")
    else:
        print("Nenhuma solução encontrada.")    