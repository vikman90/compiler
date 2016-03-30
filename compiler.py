# Compiler for C--
# Victor Manuel Fernandez Castro
# May 22, 2014

import cparser
import cfg
import sys
import regalloc
import output
from time import time

if __name__ == '__main__':
    cparser.init(open('examples/example.cmm', 'r').read())
    tStart = time()

    try:
        program = cparser.program()
        graphs = [cfg.gFunction(f) for f in program]
        output.write(graphs, 'examples/output.s')
        tEnd = time()
        print('Time:', tEnd - tStart, 'sec.')
    except SyntaxError as e:
        print('Syntax error at line', cparser.token0.line, 'near <', \
              cparser.token0.string, '>', e, file = sys.stderr)
        
