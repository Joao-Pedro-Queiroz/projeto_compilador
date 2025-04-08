import sys
import re
from abc import ABC, abstractmethod


class SymbolTable:
    def __init__(self):
        self.table = {}

    def declare(self, name, var_type):
        if name in self.table:
            raise Exception(f"Variable '{name}' already declared.")
        
        self.table[name] = (None, var_type)

    def set(self, name, value):
        if name not in self.table:
            raise Exception(f"Variable '{name}' not declared.")
        
        _, expected_type = self.table[name]
        actual_type = value[1]

        if expected_type != actual_type:
            raise TypeError(f"Type mismatch in assignment to '{name}'. Expected '{expected_type}', got '{actual_type}'.")
        
        self.table[name] = value

    def get(self, name):
        if name not in self.table:
            raise Exception(f"Variable '{name}' not declared.")
        
        value, _ = self.table[name]

        if value is None:
            raise Exception(f"Variable '{name}' used before assignment.")
        
        return self.table[name]  # (value, type)


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
        left_value, left_type = self.children[0].Evaluate(symbol_table)
        right_value, right_type = self.children[1].Evaluate(symbol_table)

        if self.value in {"+", "-", "*", "/"}:
            if left_type != "i32" or right_type != "i32":
                raise TypeError(f"Operação aritmética requer operandos 'i32', mas recebeu '{left_type}' e '{right_type}'")
            
            if self.value == "+":
                return (left_value + right_value, "i32")
            elif self.value == "-":
                return (left_value - right_value, "i32")
            elif self.value == "*":
                return (left_value * right_value, "i32")
            elif self.value == "/":
                if right_value == 0:
                    raise ZeroDivisionError("Erro: divisão por zero.")
                
                return (left_value // right_value, "i32")
        
        elif self.value in {"&&", "||"}:
            if left_type != "bool" or right_type != "bool":
                raise TypeError(f"Operação lógica requer operandos 'bool', mas recebeu '{left_type}' e '{right_type}'")
            
            if self.value == "&&":
                return (1 if left_value and right_value else 0, "bool")
            elif self.value == "||":
                return (1 if left_value or right_value else 0, "bool")
        
        elif self.value in {"==", ">", "<"}:
            if left_type != right_type:
                raise TypeError(f"Comparação requer operandos do mesmo tipo, mas recebeu '{left_type}' e '{right_type}'")
            
            if self.value == "==":
                return (1 if left_value == right_value else 0, "bool")
            elif self.value == ">":
                return (1 if left_value > right_value else 0, "bool")
            elif self.value == "<":
                return (1 if left_value < right_value else 0, "bool")
        
        elif self.value == "++":
            return (str(left_value) + str(right_value), "str")

        else:
            raise ValueError(f"Operador binário desconhecido: {self.value}")


class UnOp(Node):
    def __init__(self, value, child):
        super().__init__(value, [child])


    def Evaluate(self, symbol_table):
        value, val_type = self.children[0].Evaluate(symbol_table)

        if self.value in {"+", "-"}:
            if val_type != "i32":
                raise TypeError(f"Operador unário '{self.value}' requer tipo 'i32', mas recebeu '{val_type}'")
            
            return ((+value if self.value == "+" else -value), "i32")

        elif self.value == "!":
            if val_type != "bool":
                raise TypeError(f"Operador unário '!' requer tipo 'bool', mas recebeu '{val_type}'")
            
            return (1 if not value else 0, "bool")
        
        else:
            raise ValueError(f"Operador unário desconhecido: {self.value}")


class IntVal(Node):
    def __init__(self, value):
        super().__init__(value, [])


    def Evaluate(self, symbol_table):
         return (self.value, "i32")
    

class BoolVal(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def Evaluate(self, symbol_table):
        return (1 if self.value == "true" else 0, "bool")


class StrVal(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def Evaluate(self, symbol_table):
        return (self.value, "str")


class Identifier(Node):
    def __init__(self, value):
        super().__init__(value, [])


    def Evaluate(self, symbol_table):
        return symbol_table.get(self.value)
    

class VarDeC(Node):
    def __init__(self, identifier, type, expression=None):
        super().__init__("=", [identifier, type] + ([expression] if expression else []))


    def Evaluate(self, symbol_table):
        symbol_table.declare(self.children[0].value, self.children[1])

        if len(self.children) == 3:
            if self.children[1] != self.children[2].Evaluate(symbol_table)[1]:
                raise TypeError(f"Tipo de variável '{self.children[0].value}' não corresponde ao tipo da expressão.")
            
            value, type = self.children[2].Evaluate(symbol_table)
            symbol_table.set(self.children[0].value, (value, type))
            return (value, type)
        
        return (None, None)


class Assignment(Node):
    def __init__(self, identifier, expression):
        super().__init__("=", [identifier, expression])


    def Evaluate(self, symbol_table):
        value, type = self.children[1].Evaluate(symbol_table)
        symbol_table.set(self.children[0].value, (value, type))
        return (value, type)


class Print(Node):
    def __init__(self, expression):
        super().__init__("print", [expression])


    def Evaluate(self, symbol_table):
        value = self.children[0].Evaluate(symbol_table)
        if value[1] == "bool":
            print("true" if value[0] else "false")
        else:
            print(value[0])
        return (value, None)
    
class If(Node):
    def __init__(self, condition, then_branch, else_branch=None):
        super().__init__("if", [condition, then_branch] + ([else_branch] if else_branch else []))

    def Evaluate(self, symbol_table):
        condition_value, condition_type = self.children[0].Evaluate(symbol_table)
        
        if condition_type != "bool":
            raise TypeError(f"Condição do 'if' deve ser do tipo 'bool', mas recebeu '{condition_type}'")
        
        if condition_value:
            return self.children[1].Evaluate(symbol_table)
        elif len(self.children) > 2:
            return self.children[2].Evaluate(symbol_table)
    

class While(Node):
    def __init__(self, condition, block):
        super().__init__("while", [condition, block])

    def Evaluate(self, symbol_table):
        condition_value, condition_type = self.children[0].Evaluate(symbol_table)

        if condition_type != "bool":
            raise TypeError(f"Condição do 'while' deve ser do tipo 'bool', mas recebeu '{condition_type}'")
        
        result = None

        while condition_value:
            result = self.children[1].Evaluate(symbol_table)
            condition_value, _ = self.children[0].Evaluate(symbol_table)

        return result


class Block(Node):
    def __init__(self, statements):
        super().__init__("block", statements)


    def Evaluate(self, symbol_table):
        for statement in self.children:
            statement.Evaluate(symbol_table)

        return (None, None)


class Read(Node):
    def __init__(self):
        super().__init__("read", [])

    def Evaluate(self, symbol_table):
        value = input()

        try:
            return (int(value), "i32")
        except ValueError:
            raise ValueError(f"Entrada inválida: {value}. Esperado um número inteiro.")


class NoOp(Node):
    def __init__(self):
        super().__init__(None, [])


    def Evaluate(self, symbol_table):
        return (None, None)


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
        self.keywords = {
            "print": "PRINT", "printf": "PRINT", "if": "IF", "else": "ELSE", "while": "WHILE", 
            "reader": "READ","scanf": "READ", "var": "VAR",
            "i32": "TYPE_I32", "bool": "TYPE_BOOL", "str": "TYPE_STR",
            "true": "BOOL", "false": "BOOL"
            }
    
    def selectNext(self):
        while self.position < len(self.source) and self.source[self.position] in {' ', '\n', '\r', '\t'}:
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
            elif char == '"':
                self.position += 1
                string_val = ''

                while self.position < len(self.source) and self.source[self.position] != '"':
                    string_val += self.source[self.position]
                    self.position += 1

                if self.position >= len(self.source) or self.source[self.position] != '"':
                    raise ValueError("String não fechada corretamente com aspas.")

                self.position += 1  # Consumir aspas finais
                self.next = Token("STRING", string_val)
                return
            elif char == '+' and self.position + 1 < len(self.source) and self.source[self.position + 1] == '+':
                self.next = Token("CONCAT", '++')
                self.position += 2
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
            elif char == "=":
                if self.position + 1 < len(self.source) and self.source[self.position + 1] == "=":
                    self.next = Token("EQUAL", char * 2)
                    self.position += 1
                else:
                    self.next = Token("ASSIGN", char)
            elif char == ';': 
                self.next = Token("SEMI", char)
            elif char == ':': 
                self.next = Token("COLON", char)
            elif char == "&" and self.position + 1 < len(self.source) and self.source[self.position + 1] == "&":
                self.next = Token("AND", char * 2)
                self.position += 1
            elif char == "|" and self.position + 1 < len(self.source) and self.source[self.position + 1] == "|":
                self.next = Token("OR", char * 2)
                self.position += 1
            elif char == "!":
                self.next = Token("NOT", char)
            elif char == ">":
                self.next = Token("GREATER", char)
            elif char == "<":
                self.next = Token("LESS", char)
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
        elif token.type == "IDENTIFIER":
            self.tokenizer.selectNext()
            return Identifier(token.value)
        elif token.type == "STRING":
            self.tokenizer.selectNext()
            return StrVal(token.value)
        elif token.type == "BOOL":
            self.tokenizer.selectNext()
            return BoolVal(token.value)
        elif token.type == "PLUS":
            self.tokenizer.selectNext()
            return UnOp("+", self.parseFactor())
        elif token.type == "MINUS":
            self.tokenizer.selectNext()
            return UnOp("-", self.parseFactor())
        elif token.type == "NOT":
            self.tokenizer.selectNext()
            return UnOp("!", self.parseFactor())
        elif token.type == "LPAREN":
            self.tokenizer.selectNext()
            result = self.parseOrExpression()

            if self.tokenizer.next.type != "RPAREN":
                raise ValueError("Parênteses desbalanceados")
            
            self.tokenizer.selectNext()
            return result
        elif self.tokenizer.next.type == "READ":
            self.tokenizer.selectNext()
            
            if self.tokenizer.next.type != "LPAREN":
                raise ValueError("Parênteses esperados após 'reader'")
            
            self.tokenizer.selectNext()
            
            if self.tokenizer.next.type != "RPAREN":
                raise ValueError("Parênteses de fechamento esperados após 'reader()'")
            
            self.tokenizer.selectNext()
            return Read()
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

        while self.tokenizer.next.type in ("PLUS", "MINUS", "CONCAT"):
            operador = self.tokenizer.next.type
            self.tokenizer.selectNext()

            right = self.parseTerm()

            if operador == "PLUS":
                left = BinOp("+", left, right)
            elif operador == "MINUS":
                left = BinOp("-", left, right)
            elif operador == "CONCAT":
                left = BinOp("++", left, right)

        return left
    
    
    def parseRelationalExpression(self):
        left = self.parseExpression()

        while self.tokenizer.next.type in ("EQUAL", "GREATER", "LESS"):
            operador = self.tokenizer.next.type
            self.tokenizer.selectNext()

            right = self.parseExpression()

            if operador == "EQUAL":
                left = BinOp("==", left, right)
            elif operador == "GREATER":
                left = BinOp(">", left, right)
            elif operador == "LESS":
                left = BinOp("<", left, right)

        return left
    

    def parseAndExpression(self):
        left = self.parseRelationalExpression()

        while self.tokenizer.next.type == "AND":
            self.tokenizer.selectNext()

            right = self.parseRelationalExpression()

            left = BinOp("&&", left, right)

        return left
    

    def parseOrExpression(self):
        left = self.parseAndExpression()

        while self.tokenizer.next.type == "OR":
            self.tokenizer.selectNext()
            right = self.parseAndExpression()

            left = BinOp("||", left, right)

        return left      
    

    def parseStatement(self):
        if self.tokenizer.next.type == "SEMI":
            self.tokenizer.selectNext() 
            return NoOp()
    
        if self.tokenizer.next.type == "IDENTIFIER":
            identifier = Identifier(self.tokenizer.next.value)
            self.tokenizer.selectNext()

            if self.tokenizer.next.type == "ASSIGN":
                self.tokenizer.selectNext()
                expr = self.parseOrExpression()

                if self.tokenizer.next.type != "SEMI":
                    raise ValueError("Ponto e vírgula esperado")
                
                self.tokenizer.selectNext()
                return Assignment(identifier, expr)
        elif self.tokenizer.next.type == "PRINT":
            self.tokenizer.selectNext()
            
            if self.tokenizer.next.type != "LPAREN":
                raise ValueError("Parênteses esperados após 'print'")
            
            self.tokenizer.selectNext()
            expr = self.parseOrExpression()
            
            if self.tokenizer.next.type != "RPAREN":
                raise ValueError("Parênteses fechando esperados após condição de 'print'")
            
            self.tokenizer.selectNext()

            if self.tokenizer.next.type != "SEMI":
                raise ValueError("Ponto e vírgula esperado")

            self.tokenizer.selectNext()
            return Print(expr)
        elif self.tokenizer.next.type == "VAR":
            self.tokenizer.selectNext()

            if self.tokenizer.next.type != "IDENTIFIER":
                raise ValueError("Identificador esperado após 'var'")
            
            identifier = Identifier(self.tokenizer.next.value)
            self.tokenizer.selectNext()

            if self.tokenizer.next.type != "COLON":
                raise ValueError("Dois pontos esperados após identificador")
            
            self.tokenizer.selectNext()
            var_type = self.tokenizer.next.value

            if var_type not in {"i32", "bool", "str"}:
                raise ValueError(f"Tipo inválido: {var_type}. Esperado 'i32', 'bool' ou 'str'")
            
            self.tokenizer.selectNext()
            expression = None

            if self.tokenizer.next.type == "ASSIGN":
                self.tokenizer.selectNext()
                expression = self.parseOrExpression()

            if self.tokenizer.next.type != "SEMI":
                raise ValueError("Ponto e vírgula esperado")
            
            return VarDeC(identifier, var_type, expression)
        elif self.tokenizer.next.type == "IF":
            self.tokenizer.selectNext()
            
            if self.tokenizer.next.type != "LPAREN":
                raise ValueError("Parênteses esperados após 'if'")
            
            self.tokenizer.selectNext()
            condition = self.parseOrExpression()
            
            if self.tokenizer.next.type != "RPAREN":
                raise ValueError("Parênteses fechando esperados após condição de 'if'")
            
            self.tokenizer.selectNext()
            then_branch = self.parseBlock()
    
            else_branch = None
            
            if self.tokenizer.next.type == "ELSE":
                self.tokenizer.selectNext()
                else_branch = self.parseBlock()
            
            return If(condition, then_branch, else_branch)
        elif self.tokenizer.next.type == "WHILE":
            self.tokenizer.selectNext()
            
            if self.tokenizer.next.type != "LPAREN":
                raise ValueError("Parênteses esperados após 'while'")
            
            self.tokenizer.selectNext()
            condition = self.parseOrExpression()
            
            if self.tokenizer.next.type != "RPAREN":
                raise ValueError("Parênteses fechando esperados após condição de 'while'")
            
            self.tokenizer.selectNext()
            block = self.parseBlock()
            
            return While(condition, block)
        else:
            raise ValueError(f"Token inesperado: {self.tokenizer.next.type}")

        return NoOp()
    

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
            raise ValueError("Chave esperada para início de bloco")

        return Block(statements)
    

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