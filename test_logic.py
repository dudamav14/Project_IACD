import sys
import os

sys.path.append(os.getcwd())

from logic.csp_quiz import QuizCSP
from logic.adversarial import InterviewGame

def run_tests():
    print("=========================================")
    print(" INICIANDO TESTES DE LÓGICA (PESSOA A)")
    print("=========================================\n")

  
    print("--- [1] Gerando Dados Mock (Simulando RAG) ---")
    
    mock_question_pool = [

        {'id': 101, 'topic': 'python', 'level': 'easy',   'type': 'multiple_choice', 'category': 'vocab'},
        {'id': 102, 'topic': 'python', 'level': 'medium', 'type': 'multiple_choice', 'category': 'vocab'},
        {'id': 103, 'topic': 'python', 'level': 'hard',   'type': 'multiple_choice', 'category': 'vocab'},
        {'id': 104, 'topic': 'python', 'level': 'medium', 'type': 'multiple_choice', 'category': 'vocab'},
        
       
        {'id': 105, 'topic': 'python', 'level': 'hard',   'type': 'code_completion', 'category': 'grammar'},
        
      
        {'id': 106, 'topic': 'java',   'level': 'easy',   'type': 'multiple_choice', 'category': 'vocab'},
        
    
        {'id': 107, 'topic': 'python', 'level': 'hard',   'type': 'true_false',      'category': 'vocab'}
    ]
    print(f"Pool de perguntas carregado com {len(mock_question_pool)} itens.\n")


 
    print("--- [2] Testando CSP (Geração de Quiz) ---")
    
   
    constraints = {
        'size': 3,
        'topic': 'python',
        'max_mc': 2,      
        'min_grammar': 1   
    }
    
    print(f"Restrições aplicadas: {constraints}")
    
    csp_solver = QuizCSP(mock_question_pool, constraints)
    quiz_result = csp_solver.solve()
    
    if quiz_result:
        print(" SUCESSO: Quiz gerado!")
        print("Perguntas Escolhidas:")
        for q in quiz_result:
            print(f"  -> ID: {q['id']} | Tipo: {q['type']} | Categoria: {q['category']} | Nível: {q['level']}")
        
        types = [q['type'] for q in quiz_result]
        cats = [q['category'] for q in quiz_result]
        
        if types.count('multiple_choice') <= 2:
            print("   -> [OK] Respeitou max_mc <= 2")
        else:
            print("   -> [FALHA] Violou max_mc!")
            
        if 'grammar' in cats:
            print("   -> [OK] Respeitou min_grammar >= 1")
        else:
            print("   -> [FALHA] Violou min_grammar!")
            
    else:
        print("FALHA: O CSP não encontrou solução (Verifique a lógica).")
    print("\n")


    print("--- [3] Testando Adversarial Search (Minimax) ---")
    history = [101] 
    interview_pool = [q for q in mock_question_pool if q['topic'] == 'python']
    
    game = InterviewGame(interview_pool, history)
    
    print(f"Histórico (já perguntado): {history}")
    print("Tutor (AI) está 'pensando' usando Minimax (profundidade 2)...")
    
    
    
    best_question = game.get_best_next_question()
    
    if best_question:
        print(f" SUCESSO: O Tutor escolheu a próxima pergunta.")
        print(f"  -> ID Escolhido: {best_question['id']}")
        print(f"  -> Nível: {best_question['level']}")
        
        if best_question['level'] == 'hard':
            print("   -> [OK] O Minimax escolheu corretamente uma pergunta HARD para desafiar o aluno.")
        else:
            print(f"   -> [AVISO] O Minimax escolheu {best_question['level']}. Poderia ter sido mais agressivo?")
    else:
        print(" FALHA: Nenhuma pergunta retornada.")

if __name__ == "__main__":
    run_tests()