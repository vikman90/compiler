# Compiler lexer
# Victor Manuel Fernandez Castro
# May 12, 2014

import sys
import re

NONE = 0
COMMA = 1
SEMICOLON = 2
LPAREN = 3
RPAREN = 4
LBRACE = 5
RBRACE = 6
LBRACKET = 7
RBRACKET = 8
IF = 9
ELSE = 10
WHILE = 11
RETURN = 12
PRINT = 13
TINT = 14
TFLOAT = 15
TCHAR = 16
TVOID = 17
DOT = 18
PLUS = 19
MINUS = 20
TIMES = 21
SLASH = 22
MOD = 23
EQ = 24
SET = 25
NEQ = 26
GT = 27
GEQ = 28
LT = 29
LEQ = 30
ARRAY = 31
ID = 32
INTEGER = 33
FLOAT = 34
CHARACTER = 35
STRING = 36

patterns = [ '\s+',
             ',',
             ';',
             '\(',
             '\)',
             '\{',
             '\}',
             '\[',
             '\]',
             'if',
             'else',
             'while',
             'return',
             'print',
             'int',
             'float',
             'char',
             'void',
             '\.',
             '\+',
             '-',
             '\*',
             '/',
             '%',
             '==',
             '=',
             '!=',
             '>',
             '>=',
             '<',
             '<=',
             '([A-Za-z_]\w*)\[(\d+)\]',
             '([A-Za-z_]\w*)',
             '(\d+)',
             '(\d*\.\d+)',
             '\'(\w)\'',
             '"([^"]*)"' ]

class Token:
    def __init__(self, code, attrib, string, line):
        self.code = code
        self.attrib = attrib
        self.string = string
        self.line = line

    def __str__(self):
        return 'Line ' + str(self.line) + ' token ' + str(self.code) + \
               ' ' + str(self.string)

def lexer(strinput):
    '''Yields tuples (token, string, line)'''
    
    pos = 0
    line = 1
    error = False
    
    while strinput[pos:]:

        # Remove comments
        
        match = re.match('//', strinput[pos:])

        if match:
            pos += match.end()
            match = re.match('.*\n', strinput[pos:])

            if match:
                pos += match.end()
                line += 1
            else:
                print('Lexical error: line', line, 'near /*', \
                      file = sys.stderr)
            
            continue

        match = re.match('/\*', strinput[pos:])

        if match:
            pos += match.end()
            match = re.match('.*\*/', strinput[pos:], flags = re.DOTALL)

            if match:
                pos += match.end()
                line += match.group().count('\n')
            else:
                print('Lexical error: line', line, 'near /*', \
                      file = sys.stderr)

            continue
                         
        for i in range(len(patterns)):
            match = re.match(patterns[i], strinput[pos:])

            if match:
                pos += match.end()
                error = False

                if i == NONE:
                    line += match.group().count('\n')
                else:
                    yield Token(i, match.groups(), match.group(), line)

                break
            
        if not match:
            match = re.match('\S*', strinput[pos:])

            if not error:
                error = True
                print('Lexical error: line', line, 'near', match.group(), \
                      file = sys.stderr)
                
            pos += match.end()

if __name__ == '__main__':
    for token in lexer(open('example.cmm', 'r').read()):
        print(token)
