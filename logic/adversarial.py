import math

class InterviewGame:
    def __init__(self, available_questions, history):
        """
        :param available_questions: Lista de dicts (o pool de perguntas vindo do RAG/Banco).
                                    Deve ter a chave 'level' ('easy', 'medium', 'hard').
        :param history: Lista de IDs de perguntas que JÁ foram feitas nesta sessão.
        """
        self.questions = available_questions
        self.history = history

    def utility_function(self, question, simulated_student_performance):
        """
        Calcula o quão 'boa' é essa jogada para o Tutor (MAX).
        O Tutor quer maximizar o desafio (encontrar lacunas).
        
        Score alto = Pergunta difícil onde o aluno vai mal.
        Score baixo = Pergunta fácil ou onde o aluno vai muito bem.
        """
        level = question.get('level', 'medium') 
        
      
        level_value = 5 
        
        if level == 'hard':
            level_value = 10
        elif level == 'easy':
            level_value = 1

        # A utilidade é o Nível da Pergunta MENOS a performance do aluno.
        # Ex: Pergunta Hard (10) - Aluno vai mal (0.2 * 10) = 8 pontos para o Tutor.
        # Ex: Pergunta Easy (1) - Aluno vai bem (0.9 * 1) = 0.1 ponto para o Tutor.
        return level_value - (level_value * simulated_student_performance)

    def get_possible_moves(self):
        """ Retorna perguntas que ainda não foram usadas no histórico """
        return [q for q in self.questions if q['id'] not in self.history]

    def minimax(self, depth, is_maximizing_player, current_question=None):
        """
        Algoritmo Minimax Simplificado.
        depth: Quantos turnos à frente olhar (Tutor -> Aluno).
        """
        
        # CASO BASE: Fim da profundidade ou sem perguntas disponíveis
        possible_moves = self.get_possible_moves()
        if depth == 0 or not possible_moves:
            if current_question:
                # SIMULAÇÃO DO ALUNO (Nó folha)
                # Se a pergunta é Hard, assumimos que o aluno tem mais dificuldade (performance baixa)
                # Se é Easy, assumimos performance alta.
                # (Num sistema real, isso poderia usar o histórico real do aluno)
                base_performance = 0.5
                if current_question.get('level') == 'hard':
                    base_performance = 0.3
                elif current_question.get('level') == 'easy':
                    base_performance = 0.9
                
                return self.utility_function(current_question, base_performance)
            return 0

        if is_maximizing_player:
            # --- TURNO DO TUTOR (MAX) ---
            # Quer escolher a pergunta que resulta no maior score de utilidade
            max_eval = -math.inf
            best_move = None

            for question in possible_moves:
                # Simula fazer esta pergunta e passa a vez para o Aluno (Min)
                # Reduzimos depth em 1
                eval_score = self.minimax(depth - 1, False, question)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = question
            
            # Se estamos no topo da chamada (depth inicial), retornamos a PERGUNTA, não o score
            # Assumindo depth inicial = 2
            if depth == 2: 
                return best_move
            return max_eval

        else:
            # --- TURNO DO ALUNO (MIN) ---
            # O Aluno (simulado) jogaria para minimizar o ganho do tutor (dando a melhor resposta possível).
            # Neste modelo simplificado, o "movimento" do aluno é calculado na função de utilidade
            # então apenas passamos o valor para cima.
            return self.minimax(depth - 1, True, current_question)

    def get_best_next_question(self):
        """ Interface pública para chamar o algoritmo """
        # Verifica se há movimentos antes de chamar o minimax
        if not self.get_possible_moves():
            return None
            
        # Inicia o minimax com profundidade 2 (Pergunta do Tutor -> Resposta do Aluno)
        return self.minimax(depth=2, is_maximizing_player=True)