import sys
import re


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
                self.position -= 1
            elif char == '+':
                self.next = Token("PLUS", char)
            elif char == '-':
                self.next = Token("MINUS", char)
            else:
                raise ValueError("Caractere inválido")
            
            self.position += 1
        else:
            self.next = Token("EOF", None)


class Parser:
    def __init__(self, tokenizer: Tokenizer):
        self.tokenizer = tokenizer

    
    def parseExpression(self):
        if self.tokenizer.next.type != "INTEGER":
            raise ValueError("Expressão deve iniciar com um número.")

        result = self.tokenizer.next.value
        self.tokenizer.selectNext()

        if self.tokenizer.next.type == "INTEGER":
            raise ValueError("Dois números consecutivos sem operador são inválidos.")

        while self.tokenizer.next.type in ("PLUS", "MINUS"):
            operador = self.tokenizer.next.type
            self.tokenizer.selectNext()

            if self.tokenizer.next.type != "INTEGER":
                raise ValueError(f"Esperado um número após '{'+' if operador == 'PLUS' else '-'}'")

            if operador == "PLUS":
                result += self.tokenizer.next.value
            elif operador == "MINUS":
                result -= self.tokenizer.next.value

            self.tokenizer.selectNext()

            if self.tokenizer.next.type == "INTEGER":
                raise ValueError("Dois números consecutivos sem operador são inválidos.")

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
    
    resultado = Parser.run(expressao)
    print(f"{resultado}")