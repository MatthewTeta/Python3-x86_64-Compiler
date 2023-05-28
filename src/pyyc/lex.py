
reserved = {
    'print' : 'PRINT',
    'eval'  : 'EVAL',
    'input' : 'INPUT'
}

tokens = [
#    'PRINT',
#    'EVAL',
#    'INPUT',
    'COMMENT',
    'NAME',
    'INT',
    'EQUALS',
    'MINUS',
    'PLUS',
    'LPAR',
    'RPAR',
    'NEWLINE',
] + list(reserved.values())

# t_PRINT = r'print'
# t_EVAL  = r'eval'
# t_INPUT = r'input'
t_EQUALS = r'='
t_MINUS = r'\-'
t_PLUS = r'\+'
t_LPAR = r'\('
t_RPAR = r'\)'

def t_NAME(t):
    r'[A-Za-z_][0-9A-Za-z_]*'
    t.type = reserved.get(t.value, 'NAME')
    return t

def t_INT(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("integer value too large", t.value)
        t.value = 0
    return t

t_ignore = ' \t'

def t_COMMENT(t):
    r'\#.*'
    pass
    # No return value. Token discarded

"""def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")"""
    
def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

#def t_ID(t):
#    r'[a-zA-Z_][a-zA-Z_0-9]*'
#    t.type = reserved.get(t.value,'VARNAME')
#    return t
    
    
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

import ply.lex as lex
lexer = lex.lex()


def do_lexer(data):
    out = []
    lex.input(data)
    
    # Tokenize
    while True:
        tok = lex.token()
        if not tok: 
            break      # No more input
        out.append((tok.type,tok.value))
        
    
    return out


if __name__ == "__main__":
    import sys
    # Run a REPL to test
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
        result = do_lexer(s)
        try:
            print(result)
        except:
            continue
        if len(sys.argv) > 1:
            break