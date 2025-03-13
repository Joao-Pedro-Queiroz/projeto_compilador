import sys
import re
from abc import ABC, abstractmethod


class SymbolTable:
    def __init__(self):
        self.symbols = {}

    
    def set(self, identifier, value):
        self.symbols[identifier] = value
    

    def get(self, identifier):
        if identifier in self.symbols:
            return self.symbols[identifier]
        else:
            raise ValueError(f"Variável não definida: {identifier}")


class Node(ABC):
    def __init__(self, value, children: list):
        self.value = value
        self.children = children


    @abstractmethod
    def Evaluate(self, symbol_table):
        pass


class BinOp(Node):
    def __init__(self, value, left, right):
        super().__init__(value, [left, right])


    def Evaluate(self, symbol_table):
        left_value = self.children[0].Evaluate(symbol_table)
        right_value = self.children[1].Evaluate(symbol_table)

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


    def Evaluate(self, symbol_table):
        child_value = self.children[0].Evaluate(symbol_table)

        if self.value == "+":
            return +child_value
        elif self.value == "-":
            return -child_value
        else:
            raise ValueError(f"Operador unário desconhecido: {self.value}")


class IntVal(Node):
    def __init__(self, value):
        super().__init__(value, [])


    def Evaluate(self, symbol_table):
        return self.value


class Identifier(Node):
    def __init__(self, value):
        super().__init__(value, [])


    def Evaluate(self, symbol_table):
        return symbol_table.get(self.value)


class Assignment(Node):
    def __init__(self, identifier, expression):
        super().__init__("=", [identifier, expression])


    def Evaluate(self, symbol_table):
        value = self.children[1].Evaluate(symbol_table)
        symbol_table.set(self.children[0].value, value)
        return value


class Print(Node):
    def __init__(self, expression):
        super().__init__("print", [expression])


    def Evaluate(self, symbol_table):
        value = self.children[0].Evaluate(symbol_table)
        print(value)
        return value


class Block(Node):
    def __init__(self, statements):
        super().__init__("block", statements)


    def Evaluate(self, symbol_table):
        for statement in self.children:
            statement.Evaluate(symbol_table)


class NoOp(Node):
    def __init__(self):
        super().__init__(None, [])


    def Evaluate(self, symbol_table):
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
        self.keywords = {"print": "PRINT"}
    
    def selectNext(self):
        while self.position < len(self.source) and (self.source[self.position] == ' ' or self.source[self.position] == '\n'):
            self.position += 1

        if self.position < len(self.source):
            char = self.source[self.position]

            if char.isdigit():
                num = ''
                
                while self.position < len(self.source) and self.source[self.position].isdigit():
                    num += self.source[self.position]
                    self.position += 1
                
                if self.position < len(self.source) and self.source[self.position].isalpha():
                    raise ValueError(f"Erro de sintaxe: número seguido de letra sem separação: {num}{self.source[self.position]}")

                self.next = Token("INTEGER", int(num))
                return
            elif char.isalpha():
                ident = ''

                while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == '_'):
                    ident += self.source[self.position]
                    self.position += 1

                token_type = self.keywords.get(ident, "IDENTIFIER")

                if ident[0].isupper():
                    raise ValueError(f"Erro: Identificadores não podem começar com letra maiúscula: {ident}")
                
                self.next = Token(token_type, ident)
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
            elif char == '{': 
                self.next = Token("LBRACE", char)
            elif char == '}': 
                self.next = Token("RBRACE", char)
            elif char == '=': 
                self.next = Token("ASSIGN", char)
            elif char == ';': 
                self.next = Token("SEMI", char)
            else:
                raise ValueError("Caractere inválido")
            
            self.position += 1
        else:
            self.next = Token("EOF", None)


class Parser:
    def __init__(self, tokenizer: Tokenizer):
        self.tokenizer = tokenizer

    
    def parseBlock(self):
        statements = []

        if self.tokenizer.next.type == "LBRACE":
            self.tokenizer.selectNext()

            while self.tokenizer.next.type != "RBRACE":
                if self.tokenizer.next.type == "EOF":
                     raise ValueError("Erro de sintaxe: bloco não fechado corretamente")

                statements.append(self.parseStatement())

            self.tokenizer.selectNext()
        else:
            return NoOp()

        return Block(statements)
    

    def parseStatement(self):
        if self.tokenizer.next.type == "SEMI":
            self.tokenizer.selectNext() 
            return NoOp()
    
        if self.tokenizer.next.type == "IDENTIFIER":
            identifier = Identifier(self.tokenizer.next.value)
            self.tokenizer.selectNext()

            if self.tokenizer.next.type == "ASSIGN":
                self.tokenizer.selectNext()
                expr = self.parseExpression()

                if not isinstance(identifier, Identifier):
                    raise ValueError("Erro de sintaxe: o lado esquerdo da atribuição deve ser um identificador.")

                if self.tokenizer.next.type != "SEMI":
                    raise ValueError("Ponto e vírgula esperado")
                
                self.tokenizer.selectNext()
                return Assignment(identifier, expr)
        elif self.tokenizer.next.type == "PRINT":
            self.tokenizer.selectNext()
            expr = self.parseExpression()

            if self.tokenizer.next.type != "SEMI":
                raise ValueError("Ponto e vírgula esperado")

            self.tokenizer.selectNext()
            return Print(expr)
        elif self.tokenizer.next.type == "INTEGER":
            raise ValueError(f"Erro de sintaxe: números não podem ser usados como identificadores ({self.tokenizer.next.value})")

        return NoOp()


    def parseFactor(self):
        token = self.tokenizer.next

        if token.type == "INTEGER":
            self.tokenizer.selectNext()
            return IntVal(token.value)
        elif token.type == "IDENTIFIER":
            self.tokenizer.selectNext()
            return Identifier(token.value)
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
        root = parser.parseBlock()

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
    
    symbol_table = SymbolTable()
    root.Evaluate(symbol_table)