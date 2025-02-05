import sys
import re

class Calculadora:
    def __init__(self, expressao):
        # Verifica se há espaços entre números ou operadores inválidos
        if re.search(r'\d\s+\d', expressao):
            raise ValueError("Expressão inválida: espaços entre números.")
        
        if re.search(r'[^\d\s\+\-]', expressao):
            raise ValueError("Expressão inválida: contém caracteres inválidos.")
        
        # Remove espaços para facilitar a avaliação
        self.expressao = expressao.replace(" ", "")
    
    def evaluate(self):
        # Método público para avaliar a expressão
        return self._evaluate_recursive(self.expressao)
    
    def _evaluate_recursive(self, expr):
        """
        Método recursivo para avaliar a expressão.
        Ele busca o último operador (+ ou -) para respeitar a ordem correta.
        """
        # Base case: se a expressão for apenas um número, retorna como inteiro
        if expr.isdigit() or (expr.startswith('-') and expr[1:].isdigit()):
            return int(expr)
        
        # Operadores e suas funções associadas em um dicionário
        operadores = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y
        }
        
        # Procura o último operador para processar da direita para a esquerda
        for i in range(len(expr) - 1, -1, -1):
            if expr[i] in operadores:
                esquerda = expr[:i]
                direita = expr[i+1:]
                
                # Chamada recursiva para resolver subexpressões
                return operadores[expr[i]](self._evaluate_recursive(esquerda), self._evaluate_recursive(direita))

        # Se nenhum operador for encontrado, algo deu errado
        raise ValueError("Expressão inválida")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("Uso incorreto do programa.\nUse (exemplo): python main.py '1+2-3'")

    expressao = sys.argv[1]
    
    calculadora = Calculadora(expressao)
    resultado = calculadora.evaluate()
    print(f"{resultado}")