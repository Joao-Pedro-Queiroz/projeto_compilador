import sys
import re
from abc import ABC, abstractmethod
import os


class Code:
    def __init__(self):
        self.instructions = []

    def append(self, instruction):
        if isinstance(instruction, list):
            self.instructions.extend(instruction)
        else:
            self.instructions.append(instruction)

    def dump(self, input_filename="output.zig"):
        output_name = os.path.splitext(input_filename)[0] + ".asm"
        
        with open(output_name, "w") as f:
            f.write("section .data\n")
            f.write('   format_out db "%d", 10, 0\n')
            f.write('   format_in db "%d", 0\n')
            f.write("   scan_int dd 0\n\n")

            f.write("section .text\n\n")
            f.write("   extern printf\n")
            f.write("   extern scanf\n")
            f.write("   extern _ExitProcess@4\n")
            f.write("   global _start\n\n")
            f.write("_start:\n")
            f.write("   push ebp\n")
            f.write("   mov ebp, esp\n\n")

            for instr in self.instructions:
                f.write("   " + instr + "\n")

            f.write("\n")
            f.write("   mov esp, ebp\n")
            f.write("   pop ebp\n\n")
            f.write("   mov eax, 1\n")
            f.write("   xor ebx, ebx\n")
            f.write("   int 0x80\n")


class SymbolTable:
    def __init__(self, parent=None):
        self.parent = parent
        self.table = {}
        self.tableoffset = {}
        self.offset = 0

    def allocate(self, name, var_type):
        self.offset += 4
        self.tableoffset[name] = {"offset": self.offset, "type": var_type}
        return self.offset

    def get_offset(self, name):
        if name in self.tableoffset:
            return self.tableoffset[name]["offset"]
        elif self.parent:
            return self.parent.get_offset(name)
        else:
            raise Exception(f"Variable '{name}' not declared.")

    def declare(self, name, var_type):
        if name in self.table:
            raise Exception(f"Variable '{name}' already declared.")
        
        self.table[name] = (None, var_type)

    def set(self, name, value):
        if name in self.table:
            _, expected_type = self.table[name]
            actual_type = value[1]

            if expected_type != actual_type:
                raise TypeError(f"Type mismatch in assignment to '{name}'. Expected '{expected_type}', got '{actual_type}'.")
            
            self.table[name] = value
        elif self.parent:
            self.parent.set(name, value)
        else:
            raise Exception(f"Variable '{name}' not declared.")

    def get(self, name):
        if name in self.table:
            value, _ = self.table[name]

            if value is None:
                raise Exception(f"Variable '{name}' used before assignment.")
            
            return self.table[name]
        elif self.parent:
            return self.parent.get(name)    
        else:
            raise Exception(f"Variable '{name}' not declared.")


class Node(ABC):
    current_id = 0

    @staticmethod
    def newId():
        Node.current_id += 1
        return Node.current_id

    def __init__(self, value, children: list):
        self.value = value
        self.children = children
        self.id = Node.newId()

    @abstractmethod
    def Evaluate(self, symbol_table):
        pass

    @abstractmethod
    def Generate(self, symbol_table):
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
            if left_type == "bool" and right_type == "bool":
                return (str("true" if left_value else "false") + str("true" if right_value else "false"), "str")
            elif left_type == "bool" and right_type != "bool":
                return (str("true" if left_value else "false") + str(right_value), "str")
            elif right_type == "bool" and left_type != "bool":
                return (str(left_value) + str("true" if right_value else "false"), "str")
            else:
                return (str(left_value) + str(right_value), "str")

        else:
            raise ValueError(f"Operador binário desconhecido: {self.value}")
        
    def Generate(self, symbol_table):
        code = []
        code += self.children[1].Generate(symbol_table)  # right
        code.append("push eax")
        code += self.children[0].Generate(symbol_table)  # left
        code.append("pop ecx")

        if self.value == "+":
            code.append("add eax, ecx")
        elif self.value == "-":
            code.append("sub eax, ecx")
        elif self.value == "*":
            code.append("imul ecx")
        elif self.value == "/":
            code.append("mov edx, 0")
            code.append("idiv ecx")
        elif self.value in ["==", "<", ">"]:
            code.append("cmp eax, ecx")
            code.append("mov eax, 0")
            code.append("mov ecx, 1")

            if self.value == "==":
                code.append("cmove eax, ecx")
            elif self.value == "<":
                code.append("cmovl eax, ecx")
            elif self.value == ">":
                code.append("cmovg eax, ecx")
        elif self.value == "&&":
            code.append("test eax, eax")
            code.append("je false_and")
            code.append("test ecx, ecx")
            code.append("je false_and")
            code.append("mov eax, 1")
            code.append("jmp end_and")
            code.append("false_and:")
            code.append("mov eax, 0")
            code.append("end_and:")
        elif self.value == "||":
            code.append("test eax, eax")
            code.append("jne true_or")
            code.append("test ecx, ecx")
            code.append("jne true_or")
            code.append("mov eax, 0")
            code.append("jmp end_or")
            code.append("true_or:")
            code.append("mov eax, 1")
            code.append("end_or:")
        else:
            raise Exception("Operador binário não implementado")

        return code


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
    
    def Generate(self, symbol_table):
        code = self.children[0].Generate(symbol_table)

        if self.value == "-":
            code.append("neg eax")
        elif self.value == "!":
            code.append("cmp eax, 0")
            code.append("mov eax, 0")
            code.append("mov ecx, 1")
            code.append("cmove eax, ecx")

        return code



class IntVal(Node):
    def __init__(self, value):
        super().__init__(value, [])


    def Evaluate(self, symbol_table):
         return (self.value, "i32")
    
    def Generate(self, symbol_table):
        return ["mov eax, " + str(self.value)]
    

class BoolVal(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def Evaluate(self, symbol_table):
        return (1 if self.value == "true" else 0, "bool")
    
    def Generate(self, symbol_table):
        val = "1" if self.value == "true" else "0"
        return [f"mov eax, {val}"]


class StrVal(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def Evaluate(self, symbol_table):
        return (self.value, "str")
    
    def Generate(self, symbol_table):
        raise NotImplementedError("Strings ainda não são suportadas em código Assembly.")


class Identifier(Node):
    def __init__(self, value):
        super().__init__(value, [])


    def Evaluate(self, symbol_table):
        return symbol_table.get(self.value)
    
    def Generate(self, symbol_table):
        offset = symbol_table.get_offset(self.value)
        return [f"mov eax, [ebp-{offset}]"]
    

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
    
    def Generate(self, symbol_table):
        identifier = self.children[0].value
        type_ = self.children[1]
        offset = symbol_table.allocate(identifier, type_)

        code = [f"sub esp, 4 ; reserva espaço para {identifier}"]

        if len(self.children) == 3:
            expr_code = self.children[2].Generate(symbol_table)
            code += expr_code
            code.append(f"mov [ebp-{offset}], eax")

        return code


class Assignment(Node):
    def __init__(self, identifier, expression):
        super().__init__("=", [identifier, expression])


    def Evaluate(self, symbol_table):
        value, type = self.children[1].Evaluate(symbol_table)
        symbol_table.set(self.children[0].value, (value, type))
        return (value, type)
    
    def Generate(self, symbol_table):
        code = self.children[1].Generate(symbol_table)
        offset = symbol_table.get_offset(self.children[0].value)
        code.append(f"mov [ebp-{offset}], eax")
        return code


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
    
    def Generate(self, symbol_table):
        code = self.children[0].Generate(symbol_table)
        code.append("push eax")
        code.append("push format_out")
        code.append("call printf")
        code.append("add esp, 8")
        return code
    
    
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
        
    def Generate(self, symbol_table):
        if_id = self.id
        else_label = f"else_{if_id}"
        end_label = f"endif_{if_id}"

        code = self.children[0].Generate(symbol_table)
        code += ["cmp eax, 0"]

        if len(self.children) == 3:
            code.append(f"je {else_label}")
            code += self.children[1].Generate(symbol_table)
            code.append(f"jmp {end_label}")
            code.append(f"{else_label}:")
            code += self.children[2].Generate(symbol_table)
            code.append(f"{end_label}:")
        else:
            code.append(f"je {end_label}")
            code += self.children[1].Generate(symbol_table)
            code.append(f"{end_label}:")

        return code
    

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
    
    def Generate(self, symbol_table):
        loop_id = self.id
        start_label = f"loop_{loop_id}"
        end_label = f"exit_{loop_id}"

        code = [f"{start_label}:"]
        code += self.children[0].Generate(symbol_table)
        code += ["cmp eax, 0", f"je {end_label}"]
        code += self.children[1].Generate(symbol_table)
        code.append(f"jmp {start_label}")
        code.append(f"{end_label}:")
        return code


class Block(Node):
    def __init__(self, statements):
        super().__init__("block", statements)


    def Evaluate(self, symbol_table):
        for statement in self.children:
            if isinstance(statement, Block):
                new_scope = SymbolTable(parent=symbol_table)
                result = statement.Evaluate(new_scope)
            else:
                result = statement.Evaluate(symbol_table)

            if isinstance(statement, Return) or (
                isinstance(result, tuple) and result != (None, None)
            ):
                return result

        return (None, None)
    
    def Generate(self, symbol_table):
        code = []

        for stmt in self.children:
            code += stmt.Generate(symbol_table)

        return code


class Read(Node):
    def __init__(self):
        super().__init__("read", [])

    def Evaluate(self, symbol_table):
        value = input()

        try:
            return (int(value), "i32")
        except ValueError:
            raise ValueError(f"Entrada inválida: {value}. Esperado um número inteiro.")
        
    def Generate(self, symbol_table):
        return [
            "push scan_int",
            "push format_in",
            "call scanf",
            "add esp, 8",
            "mov eax, [scan_int]"
        ]


class FuncDec(Node):
    def __init__(self, name, parameters, return_type, body):
        super().__init__(name, parameters + [body])
        self.return_type = return_type

    def Evaluate(self, symbol_table):
        global_table = symbol_table

        while global_table.parent is not None:
            global_table = global_table.parent

        global_table.declare(self.name, self.return_type)

        global_table.set(self.name, (self, self.return_type, {"is_function": True}))

        return (None, None)

    def Generate(self, symbol_table):
        return []


class FuncCall(Node):
    def __init__(self, name, arguments):
        super().__init__(name, arguments)

    def Evaluate(self, symbol_table):
        func_entry = symbol_table.get(self.value)
        if not func_entry:
            raise Exception(f"Função '{self.value}' não declarada.")

        func_node, return_type, metadata = func_entry
        if not metadata.get("is_function", False):
            raise Exception(f"'{self.value}' não é uma função.")

        *params, body = func_node.children

        if len(params) != len(self.children):
            raise Exception(f"Função '{self.value}' esperava {len(params)} argumentos, recebeu {len(self.children)}.")

        new_scope = SymbolTable(parent=symbol_table)

        for param_node, arg_node in zip(params, self.children):
            param_name = param_node.value
            param_type = param_node.children[0]

            value, val_type = arg_node.Evaluate(symbol_table)

            if param_type != val_type:
                raise TypeError(f"Tipo do argumento '{param_name}' incompatível. Esperado '{param_type}', recebido '{val_type}'.")

            new_scope.declare(param_name, param_type)
            new_scope.set(param_name, (value, val_type))

        result = body.Evaluate(new_scope)

        if result[1] != return_type:
            raise TypeError(f"Tipo de retorno da função '{self.value}' incompatível. Esperado '{return_type}', recebido '{result[1]}'.")

        return result

    def Generate(self, symbol_table):
        return []


class Return(Node):
    def __init__(self, expression):
        super().__init__("return", [expression])

    def Evaluate(self, symbol_table):
        return self.children[0].Evaluate(symbol_table)

    def Generate(self, symbol_table):
        return []


class NoOp(Node):
    def __init__(self):
        super().__init__(None, [])


    def Evaluate(self, symbol_table):
        return (None, None)
    
    def Generate(self, symbol_table):
        return []


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
            "print": "PRINT", "printf": "PRINT",
            "if": "IF", "else": "ELSE", "while": "WHILE",
            "reader": "READ", "scanf": "READ", "var": "VAR",
            "i32": "TYPE_I32", "bool": "TYPE_BOOL", "str": "TYPE_STR",
            "true": "BOOL", "false": "BOOL", "fn": "FUNC", "return": "RETURN",
            "void": "TYPE_VOID"
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
            elif char == ",":
                self.next = Token("COMMA", char)
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
            identifier = Identifier(token.value)
            self.tokenizer.selectNext()

            if self.tokenizer.next.type == "LPAREN":
                self.tokenizer.selectNext()
                args = []

                if self.tokenizer.next.type != "RPAREN":
                    args.append(self.parseOrExpression())
                    while self.tokenizer.next.type == "COMMA":
                        self.tokenizer.selectNext()
                        args.append(self.parseOrExpression())

                if self.tokenizer.next.type != "RPAREN":
                    raise ValueError("Parêntese fechando esperado")
                self.tokenizer.selectNext()

                return FuncCall(identifier.value, args)
            
            return identifier
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
            elif self.tokenizer.next.type == "LPAREN":
                self.tokenizer.selectNext()
                args = []

                if self.tokenizer.next.type != "RPAREN":
                    args.append(self.parseOrExpression())

                    while self.tokenizer.next.type == "COMMA":
                        self.tokenizer.selectNext()
                        args.append(self.parseOrExpression())

                if self.tokenizer.next.type != "RPAREN":
                    raise ValueError("Parêntese fechando esperado")

                self.tokenizer.selectNext()

                if self.tokenizer.next.type != "SEMI":
                    raise ValueError("Ponto e vírgula esperado")

                self.tokenizer.selectNext()

                return FuncCall(identifier.value, args)
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
        elif self.tokenizer.next.type == "RETURN":
            self.tokenizer.selectNext()
            expr = self.parseOrExpression()
            return Return(expr)
        elif self.tokenizer.next.type == "VAR":
            return parseVarDec()
        elif self.tokenizer.next.type == "LBRACE":
            return parseBlock()
        else:
            raise ValueError(f"Token inesperado: {self.tokenizer.next.type}")
    

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


    def parseVarDec(self):
        if self.tokenizer.next.type == "VAR":
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


    def parseFuncDeclaration(self):
        self.tokenizer.selectNext()

        if self.tokenizer.next.type != "IDENTIFIER":
            raise ValueError("Nome da função esperado após 'func'")

        func_name = Identifier(self.tokenizer.next.value)
        self.tokenizer.selectNext()

        if self.tokenizer.next.type != "LPAREN":
            raise ValueError("Parêntese de abertura esperado após nome da função")

        self.tokenizer.selectNext()

        params = []

        if self.tokenizer.next.type != "RPAREN":
            while True:
                if self.tokenizer.next.type != "IDENTIFIER":
                    raise ValueError("Parâmetro inválido")

                param_id = Identifier(self.tokenizer.next.value)
                self.tokenizer.selectNext()

                if self.tokenizer.next.type != "COLON":
                    raise ValueError("Esperado ':' após nome do parâmetro")

                self.tokenizer.selectNext()

                param_type = self.tokenizer.next.value

                if param_type not in {"i32", "str", "bool"}:
                    raise ValueError("Tipo inválido de parâmetro")

                self.tokenizer.selectNext()
                params.append(VarDeC(param_id, param_type))

                if self.tokenizer.next.type == "COMMA":
                    self.tokenizer.selectNext()
                    continue
                elif self.tokenizer.next.type == "RPAREN":
                    break
                else:
                    raise ValueError("Vírgula ou ')' esperado após parâmetro")

        self.tokenizer.selectNext()

        if self.tokenizer.next.type != "COLON":
            raise ValueError("Esperado ':' após parâmetros da função")

        self.tokenizer.selectNext()

        return_type = self.tokenizer.next.value
        self.tokenizer.selectNext()

        if return_type not in {"i32", "str", "bool", "void"}:
            raise ValueError("Tipo inválido de função")

        body = self.parseBlock()

        return FuncDec(func_name, params, return_type, body)


    def parseProgram(self):
        children = []

        while self.tokenizer.next.type != "EOF":
            if self.tokenizer.next.type == "VAR":
                children.append(self.parseVarDec())
                self.tokenizer.selectNext()
            elif self.tokenizer.next.type == "FUNC":
                children.append(self.parseFuncDeclaration())
                self.tokenizer.selectNext()
            else:
                raise ValueError(f"Token inesperado no nível superior: {self.tokenizer.next.type}")

        return Block(children)
    

    @staticmethod
    def run(code):
        tokenizer = Tokenizer(code, 0, None)
        tokenizer.selectNext()
        parser = Parser(tokenizer)
        root = parser.parseProgram()
        main = FuncCall("main", [])

        if tokenizer.next.type != "EOF":
            raise ValueError("Erro: expressão não consumiu todos os tokens. Verifique a sintaxe.")
        
        symbol_table = SymbolTable()
        instructions = main.Evaluate(symbol_table)

    @staticmethod
    def geracodigo(code, filename):
        tokenizer = Tokenizer(code, 0, None)
        tokenizer.selectNext()
        parser = Parser(tokenizer)
        root = parser.parseProgram()
        main = FuncCall("main", [])

        if tokenizer.next.type != "EOF":
            raise ValueError("Erro: expressão não consumiu todos os tokens. Verifique a sintaxe.")

        symbol_table = SymbolTable()
        instructions = root.Generate(symbol_table)
        code_generator = Code()

        code_generator.append(instructions)
        code_generator.dump(filename)
    

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("Uso incorreto do programa.\nUse (exemplo): python main.py 'arquivo.zig'")

    arquivo = sys.argv[1]

    if not arquivo.endswith('.zig'):
        raise ValueError("O arquivo deve ter a extensão '.zig'.")

    with open(arquivo, 'r') as file:
        expressao = file.read()

    expressao = PrePro.filter(expressao)
    Parser.geracodigo(expressao, arquivo)