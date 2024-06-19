from lexer import lexer

acc = ''
c = 0
while inp := input('> '):
    for i in inp:
        if i == '(': c += 1
        elif i == ')': c -= 1
    acc += inp
    if c == 0:
        lexer.input(acc)
        for tok in lexer:
            print(tok)
