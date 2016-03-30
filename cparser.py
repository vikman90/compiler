# Compiler parser
# Victor Manuel Fernandez Castro
# May 15, 2014

import sys
import logging
import lexer
import ir
from time import time

logger = logging.getLogger('parser')
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter('parser: %(message)s'))
logger.addHandler(handler)
#logger.setLevel(logging.INFO)

loglexer = logging.getLogger('lexer')
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter('lexer: %(message)s'))
loglexer.addHandler(handler)
#loglexer.setLevel(logging.INFO)

types =  { lexer.TINT: ir.tint, lexer.TFLOAT: ir.tfloat, \
           lexer.TCHAR: ir.tchar, lexer.TVOID: ir.tvoid }
comp_opers = { lexer.EQ: '==', lexer.NEQ: '!=', lexer.GT: '>', \
               lexer.GEQ: '>=', lexer.LT: '<', lexer.LEQ: '<=' }
term_opers = { lexer.PLUS: '+', lexer.MINUS: '-' }
factor_opers = { lexer.TIMES: '*', lexer.SLASH: '/', lexer.MOD: '%' }
literals = { lexer.INTEGER: ir.tint, lexer.FLOAT: ir.tfloat, \
             lexer.CHARACTER: ir.tchar }
expr_initials = [ lexer.ID, lexer.ARRAY, lexer.LPAREN, lexer.MINUS, \
                  lexer.INTEGER, lexer.FLOAT, lexer.CHARACTER ]

def semanticError(e):
    print('Semantic error at line', str(token0.line) + ':', e, file=sys.stderr)

def init(strinput):
    '''Initialize the parser'''
    
    global lexgen, token0, token1
    lexgen = lexer.lexer(strinput)

    try:
        token0 = token1 = next(lexgen)
    except StopIteration:
        print('Warning: file empty')
        token1 = lexer.Token(lexer.NONE, None, None, None)

    nextToken()

def nextToken():
    '''Get next token from lexer'''
    
    global token0, token1
    loglexer.info(str(token0))
    token0 = token1
        
    try:
        token1 = next(lexgen)
    except StopIteration:
        token1 = lexer.Token(lexer.NONE, None, None, None)

def accept(tcode):
    '''Try to accept a token. If success, gets a new token from lexer'''
    
    if token0.code == tcode:
        nextToken()
        return True
    else:
        return False

def acceptType():
    '''Accept and return a type token. If it doesn't find it, raises an error'''
    
    try:
        stype = types[token0.code]
    except KeyError:
        raise SyntaxError('expected type')

    nextToken()
    return stype

def acceptComparator():
    '''Accept and return a comparator. If it doesn't find it, raises an error'''

    try:
        ctype = comp_opers[token0.code]
    except KeyErrpr:
        raise SyntaxError('expected comparator')

    nextToken()
    return ctype

def expect(tcode, expected):
    '''Accept a token and get the next one. If fail, raises an error'''
    
    if token0.code != tcode:
        raise SyntaxError('expected ' + expected)

    nextToken()    

################################################################################

def program():
    '''Axiom: parse a program and return a Program object'''
    
    p = ir.Program()

    while not accept(lexer.NONE):
        p.append(function())
        
    logger.info('<program> ::= { <function> } NONE')
    return p

def function():
    '''Parse a function and return a Function object'''

    global func
    stype = acceptType()

    if token0.code != lexer.ID:
        raise SyntaxError('expected id')

    try:
        func = ir.Function(token0.attrib[0], stype)
    except ir.SemanticError as e:
        semanticError(e)
        func = None
        
    nextToken()
    sp = len(ir.symtab)
    expect(lexer.LPAREN, '(')

    try:
        lvars = l_declvars()
        expect(lexer.RPAREN, ')')
    except ir.SemanticError as e:
        semanticError(e)

        while not accept(lexer.RPAREN):
            nextToken()

    try:
        b = block()
    except ir.SemanticError as e:
        semanticError(e)
        n = 1

        while n > 0:
            if token0.code == lexer.LBRACE:
                n += 1
            elif token0.code == lexer.RBRACE:
                n -= 1
            nextToken()

    if func != None:
        func.lvars = lvars
        func.block = b
        ir.symtab.pop(sp)
    
    logger.info('<function> ::= LPAREN <l_declvars> RPAREN <block>')
    return func

def l_declvars():
    '''Parse a list of variable declarations and return list(Variable)'''
    
    lvars = []
    
    if token0.code in types:
        lvars.append(declvar())

        while accept(lexer.COMMA):
            lvars.append(declvar())

        logger.info('<l_declvars> ::= <declvar> { COMMA <declvar> }')

    else:
        logger.info('<l_declvars> ::= ')
        
    return lvars

def declvar():
    '''Parse a variable declaration, returns Variable or Array'''
    
    stype = acceptType()

    if token0.code == lexer.ID:
        id_array = 1
    elif token0.code == lexer.ARRAY:
        id_array = 0
        length = token0.attrib[1]
    else:
        raise SyntaxError('expected id or array')

    name = token0.attrib[0]
    nextToken()

    if token0.code == lexer.SET:
        nextToken()

        if accept(lexer.MINUS):
            minus = True
        else:
            minus = False        

        if token0.code == lexer.INTEGER:
            value = int(token0.attrib[0])
        elif token0.code == lexer.FLOAT:
            value = float(token0.attrib[0])
        elif token0.code == lexer.CHARACTER:
            value = ord(token0.attrib[0])
        else:
            raise SyntaxError('expected constant')
        
        nextToken()

        if minus:
            value = -value

        if id_array:
            logger.info('<declvar> ::= <type> ID SET <expr>')
            return ir.Variable(name, stype, value)
            
        else:
            logger.info('<declvar> ::= <type> ID [ INTEGER ] SET <expr>')
            return ir.Array(name, stype, length, value)

    else:
        if id_array:
            logger.info('<declvar> ::= <type> ID')
            return ir.Variable(name, stype)
        else:
            logger.info('<declvar> ::= <type> ID [ INTEGER ]')
            return ir.Array(name, stype, length)

def block():
    '''Parse a block and return a Block object'''
    
    lstmt = []
    sp = len(ir.symtab)
    expect(lexer.LBRACE, '{')

    while token0.code != lexer.RBRACE:
        try:
            lstmt.append(stmt())
        except ir.SemanticError as e:
            semanticError(e)

            #while not accept(lexer.SEMICOLON):
            #    nextToken()

    expect(lexer.RBRACE, '}')
    ir.symtab.pop(sp)
    logger.info('<block> ::= LBRACE { <stmt> } RBRACE')
    return ir.Block(lstmt)

def stmt():
    '''Parse a statement and return a object of a subclass of Statement'''
    
    if token0.code == lexer.IF:
        s = cond_stmt()
        logger.info('<stmt> ::= <if_stmt>')

    elif token0.code == lexer.WHILE:
        s = loop_stmt()
        logger.info('<stmt> ::= <while_stmt>')

    elif token0.code == lexer.RETURN:
        s = return_stmt()
        logger.info('<stmt> ::= <return_stmt>')

    elif token0.code == lexer.PRINT:
        s = print_stmt()
        logger.info('<stmt> ::= <print_stmt>')

    elif token0.code == lexer.LBRACE:
        s = block()
        logger.info('<stmt> ::= <block>')

    elif token0.code == lexer.SEMICOLON:
        nextToken()
        s = ir.EmptyStmt()
        logger.info('<stmt> ::= SEMICOLON')

    elif token0.code in types:
        s = declvar();
        expect(lexer.SEMICOLON, ';')
        logger.info('<stmt> ::= <declvar> SEMICOLON')

    elif token0.code in [ lexer.ID, lexer.ARRAY ] and token1.code == lexer.SET:
        s = assign()
        logger.info('<stmt> ::= <assign>')
        
    elif token0.code in expr_initials:
        s = expr()
        expect(lexer.SEMICOLON, ';')
        logger.info('<stmt> ::= <expr> SEMICOLON')
        
    else:
        raise SyntaxError('expected statement')

    return s

def cond_stmt():
    '''Parse a conditional statement and return a CondStmt object'''
    
    expect(lexer.IF, 'if')
    expect(lexer.LPAREN, '(')
    c = cond()
    expect(lexer.RPAREN, ')')
    thenpart = stmt()

    if accept(lexer.ELSE):
        elsepart = stmt()
        logger.info('<cond_stmt> ::= IF LPAREN <cond> RPAREN <stmt> ELSE <stmt>')

    else:
        elsepart = None
        logger.info('<cond_stmt> ::= IF LPAREN <cond> RPAREN <stmt>')

    return ir.CondStmt(c, thenpart, elsepart)

def loop_stmt():
    '''Parse a loop statement and return a LoopStmt object'''
    
    expect(lexer.WHILE, 'while')
    expect(lexer.LPAREN, '(')
    c = cond()
    expect(lexer.RPAREN, ')')
    s = stmt()
    logger.info('<loop_stmt> ::= WHILE LPAREN <cond> RRPAREN <stmt>')
    return ir.LoopStmt(c, s)

def return_stmt():
    '''Parse a return statement and return a ReturnStmt object'''
    
    expect(lexer.RETURN, 'return')

    if not accept(lexer.SEMICOLON):
        e = expr()
        expect(lexer.SEMICOLON, ';')
        logger.info('<return_stmt> ::= RETURN [ <expr> ] ;')
    else:
        e = ir.Expression(ir.tvoid)
        logger.info('<return_stmt> ::= RETURN ;')
    
    return ir.ReturnStmt(e, func)
    
def print_stmt():
    '''Parse a print statement and return a PrintStmt object'''
    
    expect(lexer.PRINT, 'print')
    expect(lexer.LPAREN, '(')
    lexpr = l_expr_or_string()
    expect(lexer.RPAREN, ')')
    expect(lexer.SEMICOLON, ';')
    logger.info('<print_stmt> ::= PRINT LPAREN <l_expr_or_string> RPAREN ;')
    return ir.PrintStmt(lexpr)

def assign():
    '''Parse a assign statement and return an AssignStmt object'''
    
    if token0.code == lexer.ID:
        var = ir.VarExpr(token0.attrib[0])
        nextToken()
        expect(lexer.SET, '=')
        e = expr()
        s = ir.AssignStmt(var, e, func)
        expect(lexer.SEMICOLON, ';')
        logger.info('<assign> ::= ARRAY SET <expr>')
    elif token0.code == lexer.ARRAY:
        var = ir.ArrayExpr(token0.attrib[0], int(token0.attrib[1]))
        nextToken()
        expect(lexer.SET, '=')
        e = expr()
        s = ir.AssignStmt(var, e, func)
        expect(lexer.SEMICOLON, ';')
        logger.info('<assign> ::= ID SET <expr>')
    else:
        raise SyntaxError('expected id')

    return s

def cond():
    '''Parse a condition and return a Condition object'''
    e1 = expr()
    c = acceptComparator()
    e2 = expr()
    logger.info('<comp> ::= <expr> <comp> <expr>')
    return ir.Condition(c, e1, e2)
    
def expr():
    '''Parse an expression and return an Expression object'''
    
    e = term()

    while True:
        try:
            oper = term_opers[token0.code]
            nextToken()
            e = ir.BinExpr(oper, e, term())
        except KeyError:
            break

    logger.info('<expr> ::= <term> { (+|-) <term> }')
    return e

def term():
    '''Parse an expression of terms and return an Expression object'''
    
    e = factor()

    while True:
        try:
            oper = factor_opers[token0.code]
            nextToken()
            e = ir.BinExpr(oper, e, factor())
        except KeyError:
            break

    logger.info('<term> ::= <factor> { (*|/|%) <factor> }')
    return e

def factor():
    '''Parse an expression of factor and return an Expression object'''
    
    if accept(lexer.LPAREN):
        e = expr()
        expect(lexer.RPAREN, ')')
        logger.info('<factor> ::= ( <factor> )')
    
    elif accept(lexer.MINUS):
        e = ir.InverseExpr(factor())
        logger.info('<factor> ::= - <factor>')

    elif token0.code == lexer.ID:
        if token1.code == lexer.LPAREN:
            e = call()
            logger.info('<factor> ::= <call>')
        else:
            e = ir.VarExpr(token0.attrib[0])
            nextToken()
            logger.info('<factor> ::= ID')
        
    elif token0.code == lexer.ARRAY:
        e = ir.ArrayExpr(token0.attrib[0], int(token0.attrib[1]))
        nextToken()
        logger.info('<factor> ::= ARRAY')

    else:
        try:
            ctype = literals[token0.code]
        except KeyError:
            raise SyntaxError('expected factor')

        if token0.code == lexer.INTEGER:
            value = int(token0.attrib[0])
        elif token0.code == lexer.FLOAT:
            value = float(token0.attrib[0])
        else:
            value = ord(token0.attrib[0])
            
        nextToken()
        e = ir.ConstExpr(ctype, value)
        logger.info('<factor> ::= <literal>')

    return e

def call():
    '''Parse a call and return a CallExpr object'''
    
    if token0.code != lexer.ID:
        raise SyntaxError('expected name')

    name = token0.attrib[0]
    nextToken()
    expect(lexer.LPAREN, '(')
    lexpr = l_expr()
    expect(lexer.RPAREN, ')')
    logger.info('<call> ::= ID LPAREN <l_expr> RPAREN')
    return ir.CallExpr(name, lexpr)

def l_expr():
    '''Parse a list of expressions and return list(Exppression)'''
    
    lexpr = []
    
    if token0.code in expr_initials:
        lexpr.append(expr())

        while accept(lexer.COMMA):
            lexpr.append(expr())

        logger.info('<l_expr> ::= <expr> { COMMA <expr> } ')
        
    else:
        logger.info('<l_expr> ::= ')

    return lexpr
          
def l_expr_or_string():
    '''Parse a list of expressions or strings and return a list'''
    
    lexpr = []
    
    if token0.code == lexer.STRING:
        lexpr.append(token0.attrib[0])
        nextToken()

    elif token0.code in expr_initials:
        lexpr.append(expr())

    else:
        logger.info('<l_expr_or_string> ::= ')
        return lexpr

    while accept(lexer.COMMA):        
        if token0.code == lexer.STRING:
            lexpr.append(token0.attrib[0])
            nextToken()
        else:
            lexpr.append(expr())

    logger.info('<l_expr_or_string> ::= (<expr>|STRING) { COMMA (<expr>|STRING) }')
    return lexpr

################################################################################
    
if __name__ == '__main__':
    init(open('example.cmm', 'r').read())
    tStart = time()

    try:
        p = program()
    except SyntaxError as e:
        print('Syntax error at line', token0.line, 'near <', token0.string, \
              '>', e, file = sys.stderr)
        
    tEnd = time()
    print('Time:', tEnd - tStart, 'sec.')
