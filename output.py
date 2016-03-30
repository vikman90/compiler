# Output code
# Victor Manuel Fernandez Castro
# July 17, 2014

# r13 <- sp
# r14 <- link (ret. address)
# r15 <- pc

import logging
import sys
import ir
import regalloc

logger = logging.getLogger('output')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('output: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

NREGISTERS = 8
ARCH_BYTES = 4
FIRST_REG = 4
spillVars = { } # var -> offset(sp)
strLabels = { } # str -> label
writtenNodes = set()
stack = 0
file = None
regs = { }
curNode = None

def write(graphs, path):
    global file
    file = open(path, 'w')
    file.write('.asm\n')
    logger.info('.asm')
    labels(graphs)
    writeStrings()
    file.write('.text\n')
    logger.info('.text')

    for cfg in graphs:
        writeFunction(cfg)
    
    file.write('.end\n')
    file.close()

def labels(graphs):
    global strlabels
    labelnum = 0

    for cfg in graphs:
        for node in cfg:
            for stmt in node:
                if isinstance(stmt, ir.PrintStmt):
                    for expr in stmt.lexpr:
                        if isinstance(expr, str):
                            if not expr in strLabels:
                                strLabels[expr] = 's' + str(labelnum)
                                labelnum += 1
                            logger.info(expr + ' -> ' + strLabels[expr])

def writeStrings():
    file.write('.data\n')
    logger.info('.data')

    for string in strLabels:
        file.write(strLabels[string] + ': .string "' + string + '"\n')
        logger.info(strLabels[string] + ': .string "' + string + '"')

def writeFunction(cfg):
    global regs
    global spillVars
    global stack
    global curNode
    spillVars = { }
    toSpill = set()

    # Spill parameters and arrays

    for var in cfg.func.lvars:
        cfg.spill(var)
        toSpill.add(var)

    for node in cfg:
        for stmt in node:
            for var in node.gen | node.kill:
                if isinstance(var, ir.Array):
                    cfg.spill(var)
                    toSpill.add(var)                
    
    alloc = regalloc.Allocator(cfg, NREGISTERS)
    toSpill = alloc.toSpill()

    if len(toSpill):
        for var in toSpill:
            cfg.spill(var)
            toSpill.add(var)

    alloc = regalloc.Allocator(cfg, NREGISTERS)
    regs = alloc()
    stack = spill(toSpill, cfg.func)
    
    for node in cfg:
        curNode = node
        
        if node == cfg.first:
            if cfg.func.name == 'main':
                file.write('.global main\n')
                logger.info('.global main')
                
            file.write(cfg.func.name + ':\n')
            logger.info(cfg.func.name + ':')
            file.write('PUSH { R12 }\n')
            logger.info('PUSH { R12 }')

            if stack > 0:
                file.write('SUB SP SP #' + str(stack) + '\n')
                logger.info('SUB SP SP #' + str(stack) + '')

            initValues(cfg.func.block)
                
        writeNode(node)

        if node == cfg.last:            
            if stack > 0:
                file.write('ADD SP SP #' + str(stack) + '\n')
                logger.info('ADD SP SP #' + str(stack) + '')

        if len(node.children) == 1:
            file.write('B ' + node.children[0].getLabel() + '\n')
            logger.info('B ' + node.children[0].getLabel() + '')

def writeNode(node):
    global writtenNodes
    
    if node in writtenNodes:
        return
    
    writtenNodes.add(node)
    file.write(node.getLabel() + ':\n')
    logger.info(node.getLabel() + ':')

    for stmt in node:
        writeStatement(stmt)

def writeStatement(stmt):
    logger.info('Input: ' + str(stmt))
    if isinstance(stmt, ir.EmptyStmt):
        pass
    elif isinstance(stmt, ir.AssignStmt):
        writeAssignment(stmt)
    elif isinstance(stmt, ir.Expression):
        writeExpression(stmt)
    elif isinstance(stmt, ir.Condition):
        writeCondition(stmt)
    elif isinstance(stmt, ir.ReturnStmt):
        writeReturn(stmt)
    elif isinstance(stmt, ir.PrintStmt):
        writePrint(stmt)
    else:
        print('Error: statement ' + str(type(stmt)) + ' ( ' + str(stmt) + \
              ' ) not implemented.', file = sys.stderr)

def writeAssignment(stmt):
    global regs
    regR = writeExpression(stmt.expr) # r0, r4..r11

    if stmt.lvalue.var in regs:
        regL = regs[stmt.lvalue.var] + FIRST_REG
        file.write('MOV R' + str(regL) + ' R' + str(regR) + '\n')
        logger.info('MOV R' + str(regL) + ' R' + str(regR) + '')
    else:
        offset = spillVars[stmt.lvalue.var]
        
        if isinstance(stmt.lvalue, ir.ArrayExpr):
            offset += stmt.lvalue.index * stmt.lvalue.stype.size

        if stmt.lvalue.stype == tint:
            file.write('STR R' + str(regR) + ' [SP, #' + str(offset) + ']\n')
            logger.info('STR R' + str(regR) + ' [SP, #' + str(offset) + ']')
        elif stmt.lvalue.stype == tchar:
            file.write('STRB R' + str(regR) + ' [SP, #' + str(offset) + ']\n')
            logger.info('STRB R' + str(regR) + ' [SP, #' + str(offset) + ']')
        else:
            print('Error ( ' + str(stmt) + ' ) type unimplemented.',
                  file=sys.stderr)

def writeExpression(stmt):
    if isinstance(stmt, ir.VarExpr):
        return writeVarExpr(stmt)
    elif isinstance(stmt, ir.CallExpr):
        return writeCallExpr(stmt)
    elif isinstance(stmt, ir.ConstExpr):
        return writeConstExpr(stmt)
    elif isinstance(stmt, ir.InverseExpr):
        return writeInverseExpr(stmt)
    elif isinstance(stmt, ir.BinExpr):
        return writeBinExpr(stmt)
    else:
        print('Error: expression type unimplemented. ' + str(type(stmt)) + \
              ' ( ' + str(stmt) + ' )', file=sys.stderr)
        return 0

def writeVarExpr(stmt):
    global spillVars
    
    if stmt.var in regs:
        reg = regs[stmt.var] + FIRST_REG
        print(str(stmt.var) + ' -> REGISTER ' + str(reg), file=sys.stderr)
        return reg
    else:
        print(str(stmt.var) + ' -> STACK ' + str(spillVars[stmt.var]), file=sys.stderr)
        offset = spillVars[stmt.var]

        if isinstance(stmt.lvalue, ir.ArrayExpr):
            offset += stmt.lvalue.index * stmt.lvalue.stype.size

        if stmt.lvalue.stype == tint:
            file.write('LDR R0, [SP, #' + str(offset) + ']\n')
            logger.info('LDR R0, [SP, #' + str(offset) + ']')
        elif stmt.lvalue.stype == tfloat:
            file.write('LDRB R0, [SP, #' + str(offset) + ']\n')
            logger.info('LDRB R0, [SP, #' + str(offset) + ']')
        else:
            print('Error ( ' + str(stmt) + ' ) type unimplemented.',
                  file=sys.stderr)

        return 0

def writeCallExpr(stmt):
    saveRegisters()
    length = len(stmt.lexpr)
    
    for i in range(length - 1, -1, -1):
        reg = writeExpression(stmt.lexpr[i])
        file.write('PUSH { R' + str(reg) + ' }\n')
        logger.info('PUSH { R' + str(reg) + ' }')

    file.write('BL ' + stmt.func.name + '\n')
    logger.info('BL ' + stmt.func.name + '')

    if length > 0:
        file.write('ADD SP SP #' + str(length * ARCH_BYTES) + '\n')
        logger.info('ADD SP SP #' + str(length * ARCH_BYTES) + '')

    restoreRegisters()
    return 0

def writeConstExpr(stmt):
    if (stmt.etype == ir.tfloat):
        print('Error: float constants not implemented.', file.sys.stderr)
        return 0
    
    file.write('MOV R0 #' + str(stmt.value) + '\n')
    logger.info('MOV R0 #' + str(stmt.value) + '')
    return 0

def writeInverseExpr(stmt):
    reg = writeExpression(stmt.expr)
    file.write('MOV R1 #0\nMOV R0 R1 R' + str(reg) + '\n')
    logger.info('MOV R1 #0\nMOV R0 R1 R' + str(reg) + '')
    return 0

def writeBinExpr(stmt):
    reg1 = writeExpression(stmt.expr1)

    if reg1 == 0:
        file.write('MOV R1 R0\n')
        logger.info('MOV R1 R0')
        reg1 = 1
        
    reg2 = writeExpression(stmt.expr2)

    if stmt.oper == '+':
        file.write('ADD R0 R' + str(reg1) + ' R' + str(reg2) + '\n')
        logger.info('ADD R0 R' + str(reg1) + ' R' + str(reg2) + '')
        return 0
    elif stmt.oper == '-':
        file.write('SUB R0 R' + str(reg1) + ' R' + str(reg2) + '\n')
        logger.info('SUB R0 R' + str(reg1) + ' R' + str(reg2) + '')
        return 0
    elif stmt.oper == '*':
        file.write('MUL R0 R' + str(reg1) + ' R' + str(reg2) + '\n')
        logger.info('MUL R0 R' + str(reg1) + ' R' + str(reg2) + '')
        return 0
    else:
        print('Error: operand not implemented.', file=sys.stderr)

    return 0
    
def writeCondition(stmt):
    reg1 = writeExpression(stmt.expr1)

    if reg1 == 0:
        file.write('MOV R1 R0\n')
        logger.info('MOV R1 R0')
        reg1 = 1

    reg2 = writeExpression(stmt.expr2)

    if stmt.comp == '<=':
        file.write('ADD R' + str(reg2) + ' R' + str(reg2) + ' #1\n')
        logger.info('ADD R' + str(reg2) + ' R' + str(reg2) + ' #1')
    elif stmt.comp == '>=':
        file.write('ADD R' + str(reg1) + ' R' + str(reg1) + ' #1\n')
        logger.info('ADD R' + str(reg1) + ' R' + str(reg1) + ' #1')

    file.write('CMP R' + str(reg1) + ' R' + str(reg2) + '\n')
    logger.info('CMP R' + str(reg1) + ' R' + str(reg2) + '')

    if stmt.comp == '==':
        file.write('BEQ ' + curNode.children[0].getLabel() + '\n')
        file.write('B ' + curNode.children[1].getLabel() + '\n')
        logger.info('BEQ ' + curNode.children[0].getLabel() + '')
        logger.info('B ' + curNode.children[1].getLabel() + '')
    if stmt.comp == '!=':
        file.write('BEQ ' + curNode.children[1].getLabel() + '\n')
        file.write('B ' + curNode.children[0].getLabel() + '\n')
        logger.info('BEQ ' + curNode.children[1].getLabel() + '')
        logger.info('B ' + curNode.children[0].getLabel() + '')
    if stmt.comp == '<' or stmt.comp == '<=':
        file.write('BLT ' + curNode.children[0].getLabel() + '\n')
        file.write('B ' + curNode.children[1].getLabel() + '\n')
        logger.info('BLT ' + curNode.children[0].getLabel() + '')
        logger.info('B ' + curNode.children[1].getLabel() + '')
    if stmt.comp == '>' or stmt.comp == '>=':
        file.write('BGT ' + curNode.children[0].getLabel() + '\n')
        file.write('B ' + curNode.children[1].getLabel() + '\n')
        logger.info('BGT ' + curNode.children[0].getLabel() + '')
        logger.info('B ' + curNode.children[1].getLabel() + '')

def writeReturn(stmt):
    global stack
    reg = writeExpression(stmt.expr)

    if reg != 0:
        file.write('MOV R0 R' + str(reg) + '\n')
        logger.info('MOV R0 R' + str(reg) + '')

    if stack > 0:
        file.write('ADD SP SP #' + str(stack) + '\n')
        logger.info('ADD SP SP #' + str(stack) + '')
        
    file.write('POP { R1 }\nBX R1\n')
    logger.info('POP { R1 }\nBX R1')

def writePrint(stmt):
    print('Warning: print not implemented.', file=sys.stderr)
    
    saveRegisters()
    length = len(stmt.lexpr)
    
    for i in range(length - 1, -1, -1):
        if isinstance(stmt.lexpr[i], str):
            file.write('MOV R0, #' + strLabels[stmt.lexpr[i]] + '\n')
            logger.info('MOV R0, #' + strLabels[stmt.lexpr[i]])
        else:
            reg = writeExpression(stmt.lexpr[i])
            file.write('PUSH { R' + str(reg) + ' }\n')
            logger.info('PUSH { R' + str(reg) + ' }')

    file.write('BL print\n')
    logger.info('BL print')

    if length > 0:
        file.write('ADD SP SP #' + str(length * ARCH_BYTES) + '\n')
        logger.info('ADD SP SP #' + str(length * ARCH_BYTES) + '')

    restoreRegisters()
    return 0

def spill(toSpill, func):
    global spillVars
    stack = 0
    offset = 0

    for var in toSpill:
        if isinstance(var, ir.Array):
            stack += var.stype.size * var.length
        else:
            stack += var.stype.size

    for var in toSpill:
        if isinstance(var, ir.Array):
            offset += var.stype.size * var.length
        else:
            offset += var.stype.size

        spillVars[var] = stack - offset

    offset = stack + 4
    
    for var in func.lvars:
        spillVars[var] = offset
        offset = var.stype.size

    return stack

def initValues(block):
    for stmt in block.lstmt:
        if isinstance(stmt, ir.Variable) and not isinstance(stmt, ir.Array):
            if stmt.value != None:
                if stmt.stype == ir.tfloat:
                    print('Warning: float not implemented.', file = sys.stderr)
                elif stmt in regs:
                    file.write('MOV R' + str(regs[stmt] + FIRST_REG) + \
                               ' #' + str(stmt.value) + '\n')
                    logger.info('MOV R' + str(regs[stmt] + FIRST_REG) + \
                               ' #' + str(stmt.value))
                elif stmt in spillVars:
                    file.write('MOV R0 #' + str(stmt.value) + '\n')
                    logger.info('MOV R0 #' + str(stmt.value))
                    offset = spillVars[stmt]
                    
                    if stmt.stype == ir.tint:
                        file.write('STR R0 [SP, #' + str(offset) + ']\n')
                        logger.info('STR R0 [SP, #' + str(offset) + ']')
                    else: # ir.tchar
                        file.write('STRB R0 [SP, #' + str(offset) + ']\n')
                        logger.info('STRB R0 [SP, #' + str(offset) + ']')
        elif isinstance(stmt, ir.Block):
            initValues(stmt)
                    
def saveRegisters():
    if len(regs):
        instr = 'PUSH {'

        for reg in regs:
            instr += ' R' + str(regs[reg] + FIRST_REG)

        instr += ' }'
        file.write(instr + '\n')
        logger.info(instr)
    
def restoreRegisters():
    if len(regs):
        instr = 'POP {'

        for reg in regs:
            instr += ' R' + str(regs[reg] + FIRST_REG)

        instr += ' }'
        file.write(instr + '\n')
        logger.info(instr)
