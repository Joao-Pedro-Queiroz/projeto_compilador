import sys
import re
from abc import ABC, abstractmethod

class Node(ABC):
    def __init__(self, value, children: list):
        self.value = value
        self.children = children

    @abstractmethod
    def Evaluate(self):
        pass



class BinOp(Node):
    def __init__(self, value, left, right):
        super().__init__(value, [left, right])


    def Evaluate(self):
        left_value = self.children[0].Evaluate()
        right_value = self.children[1].Evaluate()

        if self.value == "+":
            return left_value + right_value
        elif self.value == "-":
            return left_value - right_value
        elif self.value == "*":
            return left_value * right_value
        elif self.value == "/":
            if right_value == 0:
                raise ZeroDivisionError("Erro: divisão por zero.")
            return left_value // right_value
        else:
            raise ValueError(f"Operador binário desconhecido: {self.value}")


class UnOp(Node):
    def __init__(self, value, child):
        super().__init__(value, [child])

    def Evaluate(self):
        child_value = self.children[0].Evaluate()

        if self.value == "+":
            return +child_value
        elif self.value == "-":
            return -child_value
        else:
            raise ValueError(f"Operador unário desconhecido: {self.value}")


class IntVal(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def Evaluate(self):
        return self.value


class NoOp(Node):
    def __init__(self):
        super().__init__(None, [])

    def Evaluate(self):
        return 0


class PrePro:
    @staticmethod
    def filter(code: str):
      return re.sub(r'//.*', '', code).strip()  


class Token:
    def __init__(self, type: str, value):
        self.type = type
        self.value = value


class Tokenizer:
    def __init__(self, source: str, position: int, next: Token):
        self.source = source
        self.position = position
        self.next = next
    
    def selectNext(self):
        while self.position < len(self.source) and self.source[self.position] == ' ':
            self.position += 1

        if self.position < len(self.source):
            char = self.source[self.position]

            if char.isdigit():
                num = ''
                
                while self.position < len(self.source) and self.source[self.position].isdigit():
                    num += self.source[self.position]
                    self.position += 1

                self.next = Token("INTEGER", int(num))
                return
            elif char == '+':
                self.next = Token("PLUS", char)
            elif char == '-':
                self.next = Token("MINUS", char)
            elif char == '*':
                self.next = Token("MULT", char)
            elif char == '/':
                self.next = Token("DIV", char)
            elif char == '(': 
                self.next = Token("LPAREN", char)
            elif char == ')':
                self.next = Token("RPAREN", char)
            else:
                raise ValueError("Caractere inválido")
            
            self.position += 1
        else:
            self.next = Token("EOF", None)


class Parser:
    def __init__(self, tokenizer: Tokenizer):
        self.tokenizer = tokenizer


    def parseFactor(self):
        token = self.tokenizer.next

        if token.type == "INTEGER":
            self.tokenizer.selectNext()
            return IntVal(token.value)
        elif token.type == "PLUS":
            self.tokenizer.selectNext()
            return UnOp("+", self.parseFactor())
        elif token.type == "MINUS":
            self.tokenizer.selectNext()
            return UnOp("-", self.parseFactor())
        elif token.type == "LPAREN":
            self.tokenizer.selectNext()
            result = self.parseExpression()

            if self.tokenizer.next.type != "RPAREN":
                raise ValueError("Parênteses desbalanceados")
            
            self.tokenizer.selectNext()
            return result
        else:
            raise ValueError(f"Token inesperado: {token.type}")

    
    def parseTerm(self):
        left = self.parseFactor()

        while self.tokenizer.next.type in ("MULT", "DIV"):
            operador = self.tokenizer.next.type
            self.tokenizer.selectNext()

            right = self.parseFactor()

            if operador == "MULT":
                left = BinOp("*", left, right)
            elif operador == "DIV":
                left = BinOp("/", left, right)

        return left  

    
    def parseExpression(self):
        left = self.parseTerm()

        while self.tokenizer.next.type in ("PLUS", "MINUS"):
            operador = self.tokenizer.next.type
            self.tokenizer.selectNext()

            right = self.parseTerm()

            if operador == "PLUS":
                left = BinOp("+", left, right)
            elif operador == "MINUS":
                left = BinOp("-", left, right)

        return left
    
    @staticmethod
    def run(code):
        tokenizer = Tokenizer(code, 0, None)
        tokenizer.selectNext()
        parser = Parser(tokenizer)
        root = parser.parseExpression()

        if tokenizer.next.type != "EOF":
            raise ValueError("Erro: expressão não consumiu todos os tokens. Verifique a sintaxe.")
        
        return root
    

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("Uso incorreto do programa.\nUse (exemplo): python main.py '1+2-3'")

    arquivo = sys.argv[1]

    if not arquivo.endswith('.zig'):
        raise ValueError("O arquivo deve ter a extensão '.zig'.")

    with open(arquivo, 'r') as file:
        expressao = file.read()

    expressao = PrePro.filter(expressao)
    
    root = Parser.run(expressao)

    resultado = root.Evaluate()
    print(f"{resultado}")