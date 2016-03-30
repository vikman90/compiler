# Register allocation
# Victor Manuel Fernandez Castro
# May 26, 2014

import logging
import sys

logger = logging.getLogger('regalloc')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('regalloc: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class NotEnoughRegsException(Exception):
	pass

class Allocator(dict):
    def __init__(self, cfg, nreg):
        self.cfg = cfg
        self.nreg = nreg
        self.toAlloc = {}
        cfg.liveness()

        for block in cfg:
            accessVars = block.gen | block.kill
            crossVars = (block.livein | block.liveout) - accessVars
            self.toAlloc[block] = [accessVars, crossVars]

        allVars = [self.toAlloc[block][0] | self.toAlloc[block][1] \
                   for bb in self.toAlloc]
        
        allVars2 = set()

        for v in allVars:
            allVars2 |= v

        allVars = allVars2
        self.vars = { v : None for v in allVars }
        varFreq = { v : len([bb for bb in self.toAlloc \
                             if v in self.toAlloc[bb][0] \
                             or v in self.toAlloc[bb][1]]) for v in self.vars }
        self.varFreq = sorted(varFreq, key=lambda v : varFreq[v], reverse=True)

    def toSpill(self):
        return [block for block in self.toAlloc if \
                len(self.toAlloc[block][0]) + \
                len(self.toAlloc[block][1]) > self.nreg]

    def replace(self, var, reg):
        for block in self.toAlloc:
            if var in self.toAlloc[block][0]:
                self.toAlloc[block][0].remove(var)
                self.toAlloc[block][0].add(reg)
            if var in self.toAlloc[block][1]:
                self.toAlloc[block][1].remove(var)
                self.toAlloc[block][1].add(reg)

        self.vars[var] = reg

    def usedRegs(self):
        return set([self.vars[v] for v in self.vars])

    def nextFreeReg(self):
        u = self.usedRegs()

        for i in range(self.nreg):
            if i not in u:
                return i

        raise NotEnoughRegsException('Not enough registers')

    def checkInterference(self, reg):
        for block in self.toAlloc:
            if reg in self.toAlloc[block][0] or reg in self.toAlloc[block][1]:
                return True

        return False

    def getNonInterfering(self, var):
        interfering = set()

        for block in self.toAlloc:
            theVars = self.toAlloc[block][0] | self.toAlloc[block][1]

            if var in theVars:
                interfering |= theVars

            return set(range(self.nRegs)) - interfering

    def __call__(self):
        toSpill = self.toSpill()

        if len(toSpill):
            print(toSpill)
            raise Exception('Spill has not been performed!')

        while len(self.varFreq):
            v = self.varFreq.pop(0)

            if not self.vars[v]:
                try:
                    self.replace(v, self.nextFreeReg())
                except NotEnoughRegsException:
                    candidateRegs = self.getNonInterfering(v)

                    if len(candidateRegs):
                        self.replace(v, candidateRegs[0])
                    else:
                        self.vars
                        raise Exception('A spill is needed')

        return self.vars
        
    

    
            
        
        
    
