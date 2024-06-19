import ply.lex as lex
import sys
import re

reserved = {
    'while': 'WHILE',
    'print': 'PRINT',
    'if': 'IF',
    'else': 'ELSE',
    'return': 'RETURN',
    'input': 'INPUT',
    'def': 'DEF',
    'var': 'VAR',
    'println': 'PRINTLN',
    'string': 'STRINGTYPE',
    'int': 'INTTYPE',
    'void': 'VOIDTYPE',
    'float': 'FLOATTYPE'
}
tokens = (
             'ID',
             'NUM',
             'EQ',
             'NEQ',
             'AND',
             'OR',
             'LTE',
             'GTE',
             'STRING',
             'FLOAT',
         ) + tuple(reserved.values())

literals = ('+', '-', '*', '/', '!', '<', '>', '(', ')', '=', '%', '{', '}', ';', ',', '[', ']', '$')


def t_ID(t):
    r'[a-zA-Z][a-z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_COMMENT(t):
    r'//.*'
    pass


def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


t_STRING = r'\"[^\"]*\"'
t_EQ = r'=='
t_AND = r'&&'
t_OR = r'\|\|'
t_LTE = r'<='
t_GTE = r'>='
t_NEQ = r'!='

t_ignore = '\t\r\f\v '


def t_error(t):
    print(f"Caracter ilegal {t.value[0]}")
    t.lexer.skip(1)


lexer = lex.lex()

if __name__ == '__main__':
    file = sys.argv[1]
    f = open(file, 'r+')
    lexer.input(f.read())
    f.close()
    for tok in lexer:
        print(tok)
