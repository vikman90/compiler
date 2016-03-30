.asm
.data
s0: .string "Valor de N: "
s1: .string "Resultado: %i\nTiempo: %lf seg.\n"
.text
fibonacci:
PUSH { R12 }
l0:
MOV R0 #2
CMP R4 R0
BGT l1
B l2
l1:
PUSH { R4 }
MOV R0 #1
SUB R0 R4 R0
PUSH { R0 }
BL fibonacci
ADD SP SP #4
POP { R4 }
MOV R1 R0
PUSH { R4 }
MOV R0 #2
SUB R0 R4 R0
PUSH { R0 }
BL fibonacci
ADD SP SP #4
POP { R4 }
ADD R0 R1 R0
POP { R1 }
BX R1
B l3
l3:
l2:
MOV R0 R4
POP { R1 }
BX R1
B l3
clock:
PUSH { R12 }
l4:
MOV R0 #0
POP { R1 }
BX R1
getchar:
PUSH { R12 }
l5:
MOV R0 #0
POP { R1 }
BX R1
.global main
main:
PUSH { R12 }
MOV R7 #45
l6:
PUSH { R4 R5 R6 R7 }
MOV R0, #s0
BL print
ADD SP SP #4
POP { R4 R5 R6 R7 }
PUSH { R4 R5 R6 R7 }
BL clock
POP { R4 R5 R6 R7 }
MOV R7 R0
PUSH { R4 R5 R6 R7 }
PUSH { R6 }
BL fibonacci
ADD SP SP #4
POP { R4 R5 R6 R7 }
MOV R6 R0
PUSH { R4 R5 R6 R7 }
BL clock
POP { R4 R5 R6 R7 }
MOV R4 R0
CMP R6 R6
BGT l7
B l8
l7:
CMP R6 R6
BGT l7
B l8
l8:
MOV R0 #1
SUB R0 R6 R0
MOV R6 R0
B l7
l9:
PUSH { R4 R5 R6 R7 }
SUB R0 R4 R7
MOV R1 R0
PUSH { R0 }
PUSH { R6 }
MOV R0, #s1
BL print
ADD SP SP #12
POP { R4 R5 R6 R7 }
PUSH { R4 R5 R6 R7 }
BL getchar
POP { R4 R5 R6 R7 }
MOV R0 #0
MOV R1 R0
MOV R0 #0
ADD R0 R1 R0
POP { R1 }
BX R1
MOV R0 #0
POP { R1 }
BX R1
.end
