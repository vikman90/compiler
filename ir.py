# Intermediate representation classes
# Victor Manuel Fernandez Castro
# May 19, 2014

import sys

binopers = [ '+', '-', '*', '/', '%' ]
compopers = [ '==', '!=', '>', '>=', '<', '<=' ]

class SemanticError(Exception):
    pass

################################################################################

class Type:
    def __init__(self, tname, size):
        self.tname = tname
        self.size = size

    def __repr__(self):
        return self.tname
        
class Symbol:
    def __init__(self, name, stype):
        self.name = name
        self.stype = stype

        if name in symtab:
            raise SemanticError('symbol < ' + name + ' > already in symtable')
        
        symtab.append(self)

class Variable(Symbol):
    def __init__(self, name, stype, value = None):
        super().__init__(name, stype)
        self.value = value

        if stype == tvoid:
            raise SemanticError('a variable cannot be void')

    def __repr__(self):
        string = repr(self.stype) + ' ' + self.name

        if self.value != None:
            string += ' = ' + str(self.value)

        return string

class Array(Variable):
    def __init__(self, name, stype, length, value = None):
        super().__init__(name, stype, value)
        self.length = length

    def __repr__(self):
        string = repr(self.stype) + ' ' + self.name + '[' + \
                 self.length + ']'

        if self.value != None:
            string += ' = ' + str(self.value)

        return string

class SymbolTable(list):
    def __getitem__(self, key):
        for s in self:
            if s.name == key:
                return s

        raise SemanticError('symbol < ' + key + ' > not found')
        # raise KeyError()

    def __contains__(self, item):
        for s in self:
            if s.name == item:
                return True

        return False

    def pop(self, size):
        while len(self) > size:
            super().pop()

class Function(Symbol):
    def __init__(self, name, stype, lvars = None, block = None):
        super().__init__(name, stype)
        self.lvars = lvars
        self.block = block

    def __repr__(self):
        return repr(self.stype) + ' ' + self.name + '()'

class Program(list):
    pass

class Statement:
    pass

class Block(Statement):
    def __init__(self, lstmt):
        self.lstmt = lstmt
    
class EmptyStmt(Statement):
    def __repr__(self):
        return ''

    def uses(self):
        return set()

class BranchStmt(Statement):
    def __init__(self, cond):
        self.cond = cond

    def uses(self):
        return self.cond.uses()
        
class CondStmt(BranchStmt):
    def __init__(self, cond, thenpart, elsepart):
        super().__init__(cond)
        self.thenpart = thenpart
        self.elsepart = elsepart

    def __repr__(self):
        return 'if ' + repr(self.cond) + ' // USES=' + str(self.cond.uses())

class LoopStmt(BranchStmt):
    def __init__(self, cond, stmt):
        super().__init__(cond)
        self.stmt = stmt

    def __repr__(self):
        return 'while ' + repr(self.cond) + ' // USES=' + str(self.cond.uses())

class ReturnStmt(Statement):
    def __init__(self, expr, fparent):
        self.expr = expr

        if fparent.stype is tvoid and expr.etype is not tvoid:
            print('Warning at ' + fparent.name + '(): returning expression', \
                  file = sys.stderr)
        elif fparent.stype is not tvoid and expr.etype is tvoid:
            print('Warning at ' + fparent.name + '(): void return',
                  file = sys.stderr)
        elif (expr.etype is tfloat and fparent.stype is not tfloat) or \
             (expr.etype is tint and fparent.stype is tchar):
            print('Warning at ' + fparent.name + '(): incompatible cast', \
                  file = sys.stderr)

    def __repr__(self):
        return 'return ' + repr(self.expr) + ' // USES=' + str(self.uses())

    def uses(self):
        return self.expr.uses()

class PrintStmt(Statement):
    def __init__(self, lexpr):
        self.lexpr = lexpr

    def __repr__(self):
        string = 'print('

        if len(self.lexpr) > 0:
            for expr in self.lexpr:
                string += repr(expr) + ', '

        string = string[:-2]
        return string + ')'  + ' // USES=' + str(self.uses())

    def uses(self):
        symbols = set()

        for expr in self.lexpr:
            if not isinstance(expr, str):
                symbols |= expr.uses()

        return symbols

class AssignStmt(Statement):
    def __init__(self, lvalue, expr, fparent):
        self.lvalue = lvalue
        self.expr = expr

        if expr.etype is tvoid:
            raise SemanticError('void expression')

        if (expr.etype is tfloat and lvalue.etype is not tfloat) or \
           (expr.etype is tint and lvalue.etype is tchar):
            print('Warning on ' + fparent.name + '(): incompatible type cast', \
                  file = sys.stderr)

    def __repr__(self):
        return repr(self.lvalue) + ' = ' + repr(self.expr) + ' // USES=' + \
               str(self.uses()) + ' DEFINES=' + str(self.defines())

    def defines(self):
        return {self.lvalue.var}

    def uses(self):
        return self.expr.uses()

class Expression(Statement):
    def __init__(self, etype):
        self.etype = etype

    def __repr__(self):
        return 'void'

class VarExpr(Expression):
    def __init__(self, name):
        self.var = symtab[name]

        if not isinstance(self.var, Variable):
            raise SemanticError('expected variable id')
        
        super().__init__(self.var.stype)

    def __repr__(self):
        return self.var.name

    def uses(self):
        return { self.var }

class ArrayExpr(VarExpr):
    def __init__(self, name, index):
        self.array = symtab[name]

        if not isinstance(self.array, Array):
            raise SemanticError('expected array id')

        super().__init__(name)
        self.index = index

    def __repr__(self):
        return self.array.name + '[' + repr(self.index) + ']'

class CallExpr(Expression):
    def __init__(self, name, lexpr):
        self.func = symtab[name]

        if not isinstance(self.func, Function):
            raise SemanticError('expected function id')
            
        
        super().__init__(self.func.stype)
        self.lexpr = lexpr

    def uses(self):
        return set()

    def __repr__(self):
        string = self.func.name + '('

        if len(self.lexpr) > 0:
            for expr in self.lexpr:
                string += repr(expr) + ', '

            string = string[:-2]

        return string + ')'

class ConstExpr(Expression):
    def __init__(self, ctype, value):
        super().__init__(ctype)
        self.value = value

    def __repr__(self):
        return str(self.value)

    def uses(self):
        return set()

class InverseExpr(Expression):
    def __init__(self, expr):
        super().__init__(expr.etype)
        self.expr = expr

    def __repr__(self):
        return '-' + repr(self.expr)

    def uses(self):
        return self.expr.uses()

class BinExpr(Expression):
    def __init__(self, oper, expr1, expr2):
        if oper not in binopers:
            raise SemanticError('operator not recognised')
        
        if expr1.etype is tvoid or expr2.etype is tvoid:
            raise SemanticError('binary expression with void operand')

        if expr1.etype is expr2.etype:
            etype = expr1.etype
        else:
            if expr1.etype is tfloat or expr2.etype is tfloat:
                etype = tfloat
            elif expr1.etype is tint or expr2.etype is tint:
                etype = tint
            else:
                etype = tchar

        super().__init__(etype)
        self.oper = oper
        self.expr1 = expr1
        self.expr2 = expr2

    def __repr__(self):
        return repr(self.expr1) + ' ' + self.oper + ' ' + repr(self.expr2)

    def uses(self):
        return self.expr1.uses() | self.expr2.uses()
            
class Condition:
    def __init__(self, comp, expr1, expr2):
        if comp not in compopers:
            raise SemanticError('comparator not recognised')

        if expr1.etype is tvoid or expr2.etype is tvoid:
            raise SemanticError('comparation with void operand')

        self.comp = comp
        self.expr1 = expr1
        self.expr2 = expr2

    def __repr__(self):
        return repr(self.expr1) + ' ' + self.comp + ' ' + repr(self.expr2)

    def uses(self):
        return self.expr1.uses() | self.expr2.uses()

tint = Type('int', 4)
tfloat = Type('float', 4)
tchar = Type('char', 1)
tvoid = Type('void', 0)
symtab = SymbolTable()
