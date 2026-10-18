; rg-dis disassembly -- re-assemblable m68k source
; input: niezw-raw.bin
; raw binary  org: $00006CE8  size: 310 bytes

    .cpu    68000
    .fpu    M68882
    .text
    org     $00006CE8
    MOVEM.L   D2-D3/A2-A6,-(A7)
    PEA       ($00CB7C).L
    JSR       ($006B94).L                 ; unresolved callee
    ADDQ.L    #4,A7
    MOVE.W    D0,D2
    MOVEQ     #12,D3
    LEA       ($000054).L,A2
    LEA       ($0000B2).L,A3              ; trap_12+2 (vector)
    LEA       *-686(PC),A4
    LEA       *-518(PC),A5
_L002A:
    TST.W     ($016B12).L
    BNE.S     _L005C                      ; if contents of $00016B12 != 0
    MOVE.L    D3,-(A7)
    MOVE.L    D3,-(A7)
    JSR       (A2)                        ; Indirect call; target unresolved.
    ADDQ.L    #8,A7
    MOVE.L    D0,D1
    ADD.L     D0,D1
    ADD.L     D0,D1
    LSL.L     #3,D1
    ADD.L     D0,D1
    LSL.L     #3,D1
    PEA       ($90).W
    MOVE.L    D1,-(A7)
    JSR       (A3)                        ; Indirect call; target unresolved.
    ADDQ.L    #4,A7
    MOVE.L    D0,(A7)
    JSR       (A4)                        ; Indirect call; target unresolved.
    JSR       (A5)                        ; Indirect call; target unresolved.
    SUBQ.L    #1,D3
    ADDQ.L    #4,A7
    BNE.S     _L002A
_L005C:
    SUBA.L    A2,A2
    MOVEQ     #8,D3
    LEA       ($004690).L,A3
    ANDI.L    #$FFFF,D2
    LEA       ($001EE0).L,A4
    LEA       ($002180).L,A5
    LEA       *-600(PC),A6
_L007C:
    TST.W     ($016B12).L
    BNE.S     _L00EA                      ; if contents of $00016B12 != 0
    PEA       ($500).W
    CLR.L     -(A7)
    MOVE.L    ($00CBC0).L,D0
    ADDI.L    #$3C00,D0
    MOVE.L    D0,-(A7)
    JSR       (A3)                        ; Indirect call through $00004690; target unresolved.
    LEA       $C(A7),A7
    TST.W     D3
    BEQ.S     _L011E
    MOVE.L    D2,-(A7)
    PEA       ($64).W
    MOVE.L    #$13F,D0
    SUB.L     A2,D0
    MOVE.L    D0,-(A7)
    PEA       ($63).W
    MOVE.L    A2,-(A7)
_L00B8:
    MOVE.L    ($00CBC0).L,-(A7)
    JSR       (A4)                        ; Indirect call; target unresolved.
    LEA       $18(A7),A7
    PEA       ($67).W
    PEA       ($13F).W
    PEA       ($60).W
    CLR.L     -(A7)
    JSR       (A5)                        ; Indirect call; target unresolved.
    JSR       (A6)                        ; Indirect call; target unresolved.
    LEA       $14(A2),A2
    LEA       $10(A7),A7
    DBRA      D3,_L007C
    TST.W     ($016B12).L
    BEQ.S     _L0132                      ; if contents of $00016B12 == 0
_L00EA:
    MOVEQ     #0,D0
_L00EC:
    MOVE.L    D0,-(A7)
    JSR       ($003812).L                 ; unresolved callee
    PEA       ($7D00).W
    CLR.L     -(A7)
    MOVE.L    ($00CBC0).L,-(A7)
    JSR       (A3)                        ; Indirect call; target unresolved.
    JSR       ($00225A).L                 ; unresolved callee
    PEA       ($1).W
    JSR       ($0019F8).L                 ; unresolved callee
    LEA       $14(A7),A7
    MOVEM.L   (A7)+,D2-D3/A2-A6
    dc.w    $6000
    dc.w    $FD04
_L011E:
    MOVE.L    D2,-(A7)
    PEA       ($64).W
    PEA       ($A0).W
    PEA       ($63).W
    PEA       ($9F).W
    BRA.S     _L00B8
_L0132:
    MOVEQ     #6,D0
    BRA.S     _L00EC
