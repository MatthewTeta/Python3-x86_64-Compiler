# Parser
from ast import *

from lex import tokens

precedence = (
    ('nonassoc', 'NAME'),
    ('nonassoc', 'PRINT', 'EVAL', 'INPUT'),
    ('left', 'PLUS'),
    ('right', 'UMINUS'),
)

# Program
def p_simple_program(t):
    'program : module'
    t[0] = t[1]

# Module
#def p_extra_module(t):
#    'module : module NEWLINE statement'
#    t[1].body.append(t[2])
#    t[0] = t[1]

def p_statement_module(t):
    'module : statement'   
    t[0] = Module(
        body=[
            t[1]
        ]
    )

# Simple Statements
def p_expression_statement(t):
    'statement : expression'
    t[0] = Expr(
        value=t[1]
    )

def p_assign_statement(t):
    'statement : NAME EQUALS expression'
    t[0] = Assign(
        targets=[
            Name(id=t[1], ctx=Store())
        ],
        value=t[3]
    )

def p_print_statement(t):
    'statement : PRINT expression'
    t[0] = Expr(
        value=Call(
            Name("print", Load()),
            args=[
                t[2]
            ]
        )
    )

# Expressions
def p_evalinput_expression(t):
    'expression : EVAL LPAR INPUT LPAR RPAR RPAR'
    t[0] = Call(
        func=Name('eval', ctx=Load()),
        args=[
            Call(
                func=Name('input', ctx=Load()),
                args=[]
            )
        ])

def p_paren_expression(t):
    'expression : LPAR expression RPAR'
    # This one probably has to be handled by precedence
    t[0] = t[2]
    
def p_plus_expression(t):
    'expression : expression PLUS expression'
    t[0] = BinOp(t[1], Add(), t[3])
    
def p_minus_expression(t):
    'expression : MINUS expression %prec UMINUS'
    t[0] = UnaryOp(op=USub(), operand=t[1])

def p_int_expression(t):
    'expression : INT'
    t[0] = Constant(t[1])
    
def p_name_expression(t):
    'expression : NAME'
    t[0] = Name(t[1], ctx=Load())
    
def p_empty(t):
    'empty :'
    pass


def p_error(t):
    print("Syntax error at '%s'" % t.value)


import ply.yacc as yacc
parser = yacc.yacc()

if __name__ == "__main__":
    import sys
    # Run a REPL to test
    parser = yacc.yacc()
    while True:
        try:
            if len(sys.argv) > 1:
                with open(sys.argv[1], 'r') as f:
                    s = f.read()
            else:
                s = input('python > ')
        except EOFError:
            break
        if not s: continue
        print(s, end='\n\n')
        result = parser.parse(s)
        try:
            print(dump(result, indent=2))
        except:
            continue
        if len(sys.argv) > 1:
            break
            
            
            