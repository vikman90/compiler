# Control flow graph
# Victor Manuel Fernandez Castro
# May 22, 2014

import ir
import sys
import logging

logger = logging.getLogger('cfg')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('cfg: %(message)s'))
logger.addHandler(handler)
#logger.setLevel(logging.INFO)

labelnum = 0

class Node(list):
    def __init__(self):
        self.object = object()
        self.label = None
        self.children = []
        self.livein = set()
        self.liveout = set()
        self.gen = set()
        self.kill = set()

    def hasReturn(self):
        global visited
        visited.add(self)
        
        for stmt in self:
            if isinstance(stmt, ir.ReturnStmt):
                return True

        childret = False
        
        for child in self.children:
            if child not in visited:
                if child.hasReturn():
                    childret = True
                else:
                    return False

        return childret

    def fill(self):
        '''Initializes gen and kill'''

        for stmt in self:
            uses = stmt.uses()

            if isinstance(stmt, ir.AssignStmt):
                defines = stmt.defines()
            else:
                defines = set()

            uses -= self.kill
            self.gen |= uses
            self.kill |= defines

        self.livein = set(self.gen)

    def getLabel(self):
        global labelnum
        
        if self.label == None:
            self.label = 'l' + str(labelnum)
            labelnum += 1

        return self.label

    def liveness(self):
        '''One iteration of liveness algorithm'''

        lin = len(self.livein)
        lout = len(self.liveout)

        self.liveout = set()

        for s in self.children:
            self.liveout |= s.livein

        self.livein = self.gen | (self.liveout - self.kill)
        return len(self.livein) != lin or len(self.liveout) != lout

    def __hash__(self):
        return hash(self.object)
        
class Graph:
    def __init__(self, func = None):
        self.first = Node()
        self.last = self.first
        self.func = func
        self.toSpill = set()

    def __iadd__(self, node):
        self.last += node.first
        self.last.children = node.first.children

        if node.first != node.last:
            self.last = node.last
        return self

    def __repr__(self):
        if self.name != None:
            return 'Graph object for function ' + self.func.name
        else:
            return 'Graphs object'

    def hasReturn(self):
        global visited
        visited = set()
        return self.first.hasReturn()

    def __iter__(self):
        l = []
        getBlocks(l, self.first)
        return l.__iter__()

    def liveness(self):
        changes = True
        
        for block in self:
            block.fill()

        while changes:
            changes = False
            
            for block in self:
                if block.liveness():
                    changes = True

    def spill(self, var):
        for block in self:
            block.gen.discard(var)
            block.kill.discard(var)

        self.toSpill.add(var)
    
def gFunction(func):
    '''Create a control flow graph from a function'''

    logger.info(func)
    graph = gBlock(func.block)
    graph.func = func

    if not graph.hasReturn():
        graph.last.append(ir.ReturnStmt(ir.ConstExpr(func.stype, 0), func))

        if func.stype is not ir.tvoid:
            print('Warning: function <', graph.func.name, \
                  '> has not return on some path', file=sys.stderr)
    return graph

def gStatement(stmt):
    logger.info(stmt)
    
    if isinstance(stmt, ir.Block):
        return gBlock(stmt)
    elif isinstance(stmt, ir.BranchStmt):
        return gBranch(stmt)
    elif isinstance(stmt, ir.Variable):
        return Graph()
    else:
        graph = Graph()
        graph.last.append(stmt)
        return graph
    
def gBlock(block):
    graph = Graph()

    for stmt in block.lstmt:
        graph += gStatement(stmt)

    return graph

def gBranch(stmt):
    graph = Graph()
    
    if isinstance(stmt, ir.CondStmt):
        graph.last.append(stmt.cond)
        thengraph = gStatement(stmt.thenpart)
        endgraph = Graph()
        graph.last.children.append(thengraph.first)
        thengraph.last.children.append(endgraph.first)

        if stmt.elsepart != None:
            elsegraph = gStatement(stmt.elsepart)
            graph.last.children.append(elsegraph.first)
            elsegraph.last.children.append(endgraph.first)
        else:
            graph.last.children.append(endgraph.first)
            
    elif isinstance(stmt, ir.LoopStmt):
        graph.last.append(stmt.cond)
        loopgraph = gStatement(stmt.stmt)
        endgraph = Graph()
        graph.last.children.append(graph.first)
        graph.last.children.append(loopgraph.first)
        graph.last.children.append(endgraph.first)
        loopgraph.last.children.append(graph.first)
    else:
        raise Exception('stmt is not a branch statement')

    graph.last = endgraph.last
    return graph

def getBlocks(l, node):
    if node in l:
        return

    l.append(node)

    for child in node.children:
        getBlocks(l, child)
