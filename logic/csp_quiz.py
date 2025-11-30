import time
from typing import List, Dict, Optional, Any, Tuple

class QuizCSP:
    def __init__(self, question_pool: List[Dict[str, Any]], constraints: Dict[str, Any]):
        self.pool = question_pool
        self.constraints = constraints
        self.solution = []
        self.steps_count = 0

    def is_valid(self, candidate_question):
        # 1. Duplicidade
        if candidate_question in self.solution:
            return False

        # 2. Tópico
        if 'topic' in self.constraints:
            if candidate_question.get('topic') != self.constraints['topic']:
                return False

        # 3. Tamanho Máximo
        if len(self.solution) >= self.constraints.get('size', 5):
            return False
        
        # 4. Variedade 
        if 'max_mc' in self.constraints and candidate_question.get('type') == 'multiple_choice':
            count_mc = sum(1 for q in self.solution if q.get('type') == 'multiple_choice')
            if count_mc >= self.constraints['max_mc']:
                return False

        return True

    def check_final_goal(self):
        count_hard = sum(1 for q in self.solution if q.get('level') == 'hard')
        min_hard = self.constraints.get('min_hard', 0)
        if count_hard < min_hard:
            return False

        if 'min_grammar' in self.constraints:
            count_grammar = sum(1 for q in self.solution if q.get('category') == 'grammar')
            if count_grammar < self.constraints['min_grammar']:
                return False
        
        return True
    
    def solve(self) -> Tuple[Optional[List[Dict]], Dict[str, Any]]:
        start_time = time.time()
        self.steps_count = 0 
        
        result = self._backtracking_search()
        
        end_time = time.time()
        stats = {
            "success": result is not None,
            "time_seconds": end_time - start_time,
            "steps_explored": self.steps_count,
            "quiz_size": len(result) if result else 0
        }
        return result, stats
    
    def _backtracking_search(self):
        self.steps_count += 1
        
        target_size = self.constraints.get('size', 5)
        
        if len(self.solution) == target_size:
            if self.check_final_goal():
                return self.solution
            else:
                return None

        for question in self.pool:
            if self.is_valid(question):
                self.solution.append(question)
                result = self._backtracking_search() 
                
                if result is not None:
                    return result
                
                self.solution.pop() 

        return None

if __name__ == "__main__":
    mock_pool = [
        {'id': 1, 'topic': 'python', 'level': 'easy', 'type': 'multiple_choice', 'category': 'vocab'},
        {'id': 2, 'topic': 'python', 'level': 'hard', 'type': 'multiple_choice', 'category': 'vocab'},
        {'id': 3, 'topic': 'python', 'level': 'medium', 'type': 'multiple_choice', 'category': 'vocab'},
        {'id': 4, 'topic': 'python', 'level': 'hard', 'type': 'multiple_choice', 'category': 'vocab'},
        {'id': 5, 'topic': 'python', 'level': 'medium', 'type': 'code_completion', 'category': 'grammar'},
    ]
    regras = {'size': 3, 'topic': 'python', 'max_mc': 2, 'min_grammar': 1}
    solver = QuizCSP(mock_pool, regras)
    quiz, stats = solver.solve()
    
    if quiz:
        print(f"Sucesso! Passos: {stats['steps_explored']}")
        for q in quiz:
            print(q)
    else:
        print("Falha.")