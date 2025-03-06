import sys
import re
from abc import ABC, abstractmethod

class Node(ABC):
    def __init__(self, value, children=[]):
        self.value = value
        self.children = children

    @abstractmethod
    def Evaluate(self):
        pass


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
            return token.value
        elif token.type == "PLUS":
            self.tokenizer.selectNext()
            return +self.parseFactor()
        elif token.type == "MINUS":
            self.tokenizer.selectNext()
            return -self.parseFactor()
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
        result = self.parseFactor()

        while self.tokenizer.next.type in ("MULT", "DIV"):
            operador = self.tokenizer.next.type
            self.tokenizer.selectNext()

            termo = self.parseFactor()

            if operador == "MULT":
                result *= termo
            elif operador == "DIV":
                if termo == 0:
                    raise ZeroDivisionError("Divisão por zero não permitida.")

                result //= termo

        return result

    
    def parseExpression(self):
        result = self.parseTerm()

        while self.tokenizer.next.type in ("PLUS", "MINUS"):
            operador = self.tokenizer.next.type
            self.tokenizer.selectNext()

            termo = self.parseTerm()

            if operador == "PLUS":
                result += termo
            elif operador == "MINUS":
                result -= termo

        return result
    
    @staticmethod
    def run(code):
        tokenizer = Tokenizer(code, 0, None)
        tokenizer.selectNext()
        parser = Parser(tokenizer)
        result = parser.parseExpression()

        if tokenizer.next.type != "EOF":
            raise ValueError("Erro: expressão não consumiu todos os tokens. Verifique a sintaxe.")
        
        return result
    

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("Uso incorreto do programa.\nUse (exemplo): python main.py '1+2-3'")

    expressao = sys.argv[1]

    expressao = PrePro.filter(expressao)
    
    resultado = Parser.run(expressao)
    print(f"{resultado}")