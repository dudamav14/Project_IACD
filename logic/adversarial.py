import math
import time
from typing import List, Dict, Optional, Any, Tuple

class InterviewGame:
    def __init__(self, available_questions: List[Dict[str, Any]], history: List[int]):
        """
        :param available_questions: Lista de dicts (o pool de perguntas vindo do RAG/Banco).
        :param history: Lista de IDs de perguntas que JÁ foram feitas.
        """
        self.questions = available_questions
        self.history = history
        self.nodes_visited = 0  

    def utility_function(self, question: Dict, simulated_student_performance: float) -> float:
        """
        Calcula a utilidade. Defensivo contra chaves em falta.
        """
        level = question.get('level', 'medium')
        
        level_value = 5
        if level == 'hard':
            level_value = 10
        elif level == 'easy':
            level_value = 1
            
        return level_value - (level_value * simulated_student_performance)

    def get_possible_moves(self) -> List[Dict]:
        return [q for q in self.questions if q['id'] not in self.history]

    def minimax(self, depth: int, is_maximizing_player: bool, current_question: Optional[Dict] = None) -> Any:
        """
        Minimax com contagem de nós visitados.
        """
        self.nodes_visited += 1  
        
        possible_moves = self.get_possible_moves()
        if depth == 0 or not possible_moves:
            if current_question:
                base_performance = 0.5
                lvl = current_question.get('level', 'medium')
                
                if lvl == 'hard':
                    base_performance = 0.3
                elif lvl == 'easy':
                    base_performance = 0.9
                
                return self.utility_function(current_question, base_performance)
            return 0

        if is_maximizing_player:
            max_eval = -math.inf
            best_move = None

            for question in possible_moves:
                eval_score = self.minimax(depth - 1, False, question)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = question
            
            if depth == 2: 
                return best_move
            return max_eval

        else:
            return self.minimax(depth - 1, True, current_question)

    def get_best_next_question(self) -> Tuple[Optional[Dict], Dict[str, Any]]:
        
        """
        Retorna a melhor pergunta E as estatísticas de execução.
        """
        start_time = time.time()
        self.nodes_visited = 0
        
        if not self.get_possible_moves():
            return None, {"success": False, "reason": "No questions available"}
            
        best_question = self.minimax(depth=2, is_maximizing_player=True)
        
        end_time = time.time()
         
        stats = {
            "success": True,
            "time_seconds": end_time - start_time,
            "nodes_visited": self.nodes_visited,
            "algorithm": "Minimax (Depth 2)"
        }
        
        return best_question, stats