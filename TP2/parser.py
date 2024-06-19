import ply.yacc as yacc
import sys, tempfile
from envManager import EnvManager
from lexer import tokens

output = tempfile.TemporaryFile()
env = EnvManager()
inside_fun = []
has_return = [False]

precedence = (
    ('left', 'AND', 'OR', 'EQ', 'NEQ'),
    ('left', 'GTE', 'LTE', '>', '<'),
    ('left', '+', '-', '$'),
    ('left', '*', '/', '%'),
    ('left', 'UMINUS', '!'),
    ('left', 'INDEX'),
)


def p_program(p):
    '''program : declist start funlist entrypoint stmtlist '''
    output.write(b'STOP')


def p_start(p):
    '''start :'''
    output.write(b'JUMP entrypoint\n')


def p_entrypoint(p):
    '''entrypoint :'''
    output.write(b'entrypoint:\n')


def p_fun(p):
    '''fun : DEF fun_name '(' funargs ')' ftype '{' stmtlist '}' '''
    if not has_return[0] and inside_fun[1] is not None:
        print('no return statement inside funtion')
        raise SyntaxError
    output.write(b'RETURN\n')
    env.add_fun(p[2], p[4], p[6])
    env.pop_fun_scope()
    inside_fun.clear()


def p_fun_name(p):
    '''fun_name : ID '''
    if env.fun_exists(p[1]):
        print('cannot redeclare function')
        parser.success = False
        raise SyntaxError
    output.write(f'{p[1]}:\n'.encode('ascii'))
    inside_fun.append(p[1])
    p[0] = p[1]


def p_ftype(p):
    '''ftype : type'''
    inside_fun.append(p[1])
    p[0] = p[1]


# - declaracoes

def p_stmt_print(p):
    '''stmt : PRINT '(' expr ')' ';' '''
    d = {int: b'WRITEI\n', str: b'WRITES\n', float: b'WRITEF\n'}
    if p[3] not in d:
        print('cannot print value')
        raise SyntaxError
    output.write(d[p[3]])


def p_stmt_println(p):
    '''stmt : PRINTLN '(' ')' ';' 
            | PRINTLN '(' expr ')' ';' '''
    if len(p) > 5:
        d = {int: b'WRITEI\n', str: b'WRITES\n', float: b'WRITEF\n'}
        if p[3] not in d:
            print('cannot print value')
            raise SyntaxError
        output.write(d[p[3]])
    output.write(b'WRITELN\n')


def p_stmt_while(p):
    '''stmt : WHILE new_label '(' expr ')' jz block '''
    if p[4] != int:
        print('Type mismatch line:', p.lineno(4))
        raise SyntaxError
    output.write(f'JUMP lbl{p[2]}\n'.encode())
    output.write(f'lbl{p[6]}:\n'.encode())
    env.pop_jz_label()


def p_stmt_ifelse(p):
    '''stmt : IF '(' expr ')' jz block
            | IF '(' expr ')' jz block ELSE jmp jz_label block '''
    if p[3] != int:
        print('Type mismatch line:', p.lineno(3))
        raise SyntaxError
    if len(p) == 7:
        output.write(f'lbl{env.get_label()}:\n'.encode('ascii'))
    else:
        output.write(f'lbl{p[8]}:\n'.encode())


def p_jmp(p):
    '''jmp :'''
    env.new_label()
    output.write(f'JUMP lbl{env.get_label()}\n'.encode('ascii'))
    p[0] = env.get_label()


def p_jz(p):
    '''jz :'''
    env.new_label()
    output.write(f'JZ lbl{env.get_label()}\n'.encode('ascii'))
    env.push_jz_label()
    p[0] = env.get_label()


def p_jz_label(p):
    '''jz_label :'''
    output.write(f'lbl{env.pop_jz_label()}:\n'.encode('ascii'))


def p_new_label(p):
    '''new_label :'''
    env.new_label()
    output.write(f'lbl{env.get_label()}:\n'.encode())
    p[0] = env.get_label()


def p_declare_arr1(p):
    '''var_declare : VAR ID '[' NUM ']' type ';' '''
    if env.var_exists(p[2]):
        print(f'cannot redeclare identifier {p[2]}')
        parser.success = False
        raise SyntaxError
    env.add_var(p[2], [p[6]], p[4])
    output.write(f'PUSHN {p[4]}\n'.encode('ascii'))


def p_declare_arr2(p):
    '''var_declare : VAR ID '[' NUM ']' '[' NUM ']' type ';' '''
    if env.var_exists(p[2]):
        print(f'cannot redeclare identifier {p[2]}')
        parser.success = False
        raise SyntaxError
    env.add_var(p[2], [[p[9]]], p[4] * p[7])
    output.write(f'PUSHN {p[4]}\n'.encode('ascii'))
    address, typ = env.get_var(p[2])
    for i in range(p[4]):
        ad = env.add_var(None, None, p[7])
        output.write(b'PUSHGP\n')
        output.write(f'PUSHI {ad}\n'.encode('ascii'))
        output.write(b'PADD\n')
        output.write(f'STOREG {address + i}\n'.encode('ascii'))
        output.write(f'PUSHN {p[7]}\n'.encode('ascii'))


def p_declare_var(p):
    '''var_declare : VAR ID type '=' expr ';'
                   | VAR ID type ';' '''
    if env.var_exists(p[2]):
        print(f'cannot redeclare identifier {p[2]}')
        parser.success = False
        raise SyntaxError
    if len(p) == 7:
        if p[5] != p[3]:
            print('Type mismatch line:', p.lineno(1))
            parser.success = False
            raise SyntaxError
    else:
        if p[3] == float:
            output.write(b'PUSHF 0.0')
        else:
            output.write(b'PUSHI 0\n')
    env.add_var(p[2], p[3])


def p_stmt_assign(p):
    '''stmt : ID '=' expr ';' '''
    if not env.var_exists(p[1]):
        print(f'variable {p[1]} has not been declared')
        parser.success = False
        raise SyntaxError
    address, typ = env.get_var(p[1])
    if typ != p[3]:
        print('Type mismatch line:', p.lineno(1))
        parser.success = False
        raise SyntaxError
    if address < 0:
        output.write(f'STOREL {address}\n'.encode('ascii'))
    else:
        output.write(f'STOREG {address}\n'.encode('ascii'))


def p_stmt_assign_arr(p):
    '''stmt : expr '[' expr ']' '=' expr ';' '''
    if type(p[1]) != list or p[1][0] != p[6] or p[3] != int:
        print('Type mismatch line:', p.lineno(1))
        parser.success = False
        raise SyntaxError
    output.write(b'STOREN\n')


def p_stmt_return(p):
    '''stmt : RETURN expr ';' 
            | RETURN ';' '''
    if not inside_fun:
        print('can only return inside of a function')
        parser.success = False
        raise SyntaxError
    typ = p[2] if len(p) == 4 else None
    if typ != inside_fun[1]:
        print('Type mismatch line:', p.lineno(1))
        parser.success = False
        raise SyntaxError
    has_return[0] = True
    output.write(b'RETURN\n')


def p_stmt_expr(p):
    '''stmt : expr ';' '''


# --------------------------

# - expressoes

def p_expr_input(p):
    '''expr : INPUT '(' ')' '''
    output.write(b'READ\n')
    p[0] = str


def p_expr_str(p):
    '''expr : STRINGTYPE '(' expr ')' '''
    d = {str: b'', int: b'STRI\n', float: b'STRF\n'}
    if p[3] not in d:
        print('Type mismatch line:', p.lineno(1))
        parser.success = False
        raise SyntaxError
    output.write(d[p[3]])
    p[0] = str


def p_expr_atoi(p):
    '''expr : INTTYPE '(' expr ')' '''
    d = {str: b'ATOI\n', float: b'FTOI\n', int: b''}
    if p[3] not in d:
        print('Type mismatch line:', p.lineno(1))
        parser.success = False
        raise SyntaxError
    output.write(d[p[3]])
    p[0] = int

def p_expr_ftoi(p):
    '''expr : FLOATTYPE '(' expr ')' '''
    d = {str: b'ATOF\n', int: b'ITOF\n', float: b''}
    if p[3] not in d:
        print('Type mismatch line:', p.lineno(1))
        parser.success = False
        raise SyntaxError
    output.write(d[p[3]])
    p[0] = float



def p_expr_binop(p):
    '''expr : expr '+' expr 
            | expr '-' expr
            | expr '*' expr 
            | expr '/' expr
            | expr '>' expr
            | expr '<' expr 
            | expr GTE expr
            | expr LTE expr 
            | expr EQ expr
            | expr NEQ expr '''
    ops = {'+': b'ADD\n',
           '-': b'SUB\n',
           '*': b'MUL\n',
           '/': b'DIV\n',
           '>': b'SUP\n',
           '<': b'INF\n',
           '>=': b'SUPEQ\n',
           '<=': b'INFEQ\n',
           '==': b'EQUAL\n',
           '!=': b'EQUAL\nNOT\n'}
    if p[1] != p[3] or p[1] not in [float, int]:
        print('Type mismatch line:', p.lineno(1))
        parser.success = False
        raise SyntaxError
    op = ops[p[2]]
    if p[1] == float and p[2] not in ['!=', '==']:
        op = ('F'+op.decode('ascii')).encode('ascii')
    output.write(op)
    if p[2] == '/' and p[1] == int:
        output.write(b'FTOI\n')
    p[0] = p[1]

def p_expr_binop_int(p):
    '''expr : expr '%' expr
            | expr AND expr
            | expr OR expr'''
    if p[1] != int or p[3] != int:
        print('Type mismatch line:', p.lineno(1))
        parser.success = False
        raise SyntaxError
    ops = {'||': b'OR\n', '&&': b'AND\n', '%': b'MOD\n'}
    output.write(ops[p[2]])
    p[0] = int

def p_expr_concat(p):
    '''expr : expr '$' expr'''
    if p[1] != str or p[3] != str:
        print('Type mismatch line:', p.lineno(1))
        parser.success = False
        raise SyntaxError
    output.write(b'CONCAT\n')
    p[0] = str
def p_expr_not(p):
    '''expr : '!' expr '''
    if p[2] != int:
        print('Type mismatch line:', p.lineno(1))
        parser.success = False
        raise SyntaxError
    output.write(b'NOT\n')
    p[0] = int


def p_expr_neg(p):
    '''expr : '-' expr %prec UMINUS '''
    if p[2] not in [int, float]:
        print('Type mismatch line:', p.lineno(1))
        parser.success = False
        raise SyntaxError
    if p[2] == float:
        output.write(b'PUSHF -1.0\n')
        output.write(b'FMUL\n')
    else:
        output.write(b'PUSHI -1\n')
        output.write(b'MUL\n')
    p[0] = p[2]


def p_expr_id(p):
    '''expr : ID '''
    if not env.var_exists(p[1]):
        print(f'Unknown identifier {p[1]}')
        parser.success = False
        raise SyntaxError
    address, typ = env.get_var(p[1])
    if type(typ) == list and p[1] not in env.fun_scope:
        output.write(b'PUSHGP\n')
        output.write(f'PUSHI {address}\n'.encode('ascii'))
        output.write(b'PADD\n')
    else:
        if address < 0:
            output.write(f'PUSHL {address}\n'.encode('ascii'))
        else:
            output.write(f'PUSHG {address}\n'.encode('ascii'))
    p[0] = typ


def p_expr_ind(p):
    '''expr : expr '[' expr ']' %prec INDEX '''
    if type(p[1]) != list or p[3] != int:
        print('Type mismatch line:', p.lineno(1))
        parser.success = False
        raise SyntaxError
    output.write(b'LOADN\n')
    p[0] = p[1][0]


def p_expr_string(p):
    '''expr : STRING '''
    output.write(f'PUSHS {p[1]}\n'.encode('ascii'))
    p[0] = str


def p_expr_num(p):
    '''expr : NUM '''
    output.write(f'PUSHI {p[1]}\n'.encode('ascii'))
    p[0] = int

def p_expr_float(p):
    '''expr : FLOAT'''
    output.write(f'PUSHF {p[1]}\n'.encode('ascii'))
    p[0] = float


def p_expr_fun(p):
    '''expr : ID '(' fcall ')' '''
    if not env.fun_exists(p[1]):
        parser.success = False
        print(f'Unknown function call {p[1]}')
        raise SyntaxError
    if env.get_fun_type(p[1]) != p[3]:
        print('Type mismatch line:', p.lineno(1))
        parser.success = False
        raise SyntaxError
    output.write(f'PUSHA {p[1]}\n'.encode('ascii'))
    output.write(b'CALL\n')
    p[0] = env.get_fun_return(p[1])

def p_expr(p):
    '''expr : '(' expr ')' '''
    p[0] = p[2]


# ------------------------

def p_type_string(p):
    '''type : STRINGTYPE'''
    p[0] = str


def p_type_int(p):
    '''type : INTTYPE'''
    p[0] = int


def p_type_void(p):
    '''type : VOIDTYPE'''

def p_type_float(p):
    '''type : FLOATTYPE'''
    p[0] = float


def p_type_arr(p):
    '''type :  type '[' ']'  '''
    p[0] = [p[1]]


def p_declist(p):
    '''declist : declist var_declare
               |'''


def p_funlist(p):
    '''funlist : funlist fun 
               |'''


def p_stmtlist(p):
    '''stmtlist : stmtlist stmt 
                |'''


def p_funargs(p):
    ''' funargs : idlist
                 |'''
    p[0] = [] if len(p) == 1 else p[1]
    env.set_fun_arg_length(len(p[0]))


def p_idlist(p):
    '''idlist : idlist ',' ID type
              | ID type '''
    if len(p) == 3:
        env.add_fun_var(p[1], p[2])
        p[0] = [p[2]]
    else:
        env.add_fun_var(p[3], p[4])
        p[0] = p[1] + [p[4]]


def p_fcall(p):
    '''fcall : exprlist
             |'''
    p[0] = [] if len(p) == 1 else p[1]


def p_exprlist(p):
    '''exprlist : exprlist ',' expr
                | expr '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_block(p):
    '''block : '{' stmtlist '}' 
             | stmt '''


def p_error(p):
    parser.success = False
    print(f'Syntax error at token {p.type} line {p.lineno}')


parser = yacc.yacc(start='program')

# linha de comandos

if __name__ == '__main__':
    file = sys.argv[1]
    if file == '-g':
        for i in parser.productions:
            print(i)
        sys.exit(0)
    f = open(file, 'r+')
    try:
        parser.success = True
        res = parser.parse(f.read())
        if parser.success:
            output.seek(0)
            print(output.read().decode())
    except Exception as e:
        raise
    output.flush()
    output.close()
    f.close()
