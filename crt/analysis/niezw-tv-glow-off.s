; rg-dis disassembly -- re-assemblable m68k source
; input: niezw-raw.bin
; raw binary  org: $00006E8A  size: 440 bytes

    .cpu    68000
    .fpu    M68882
    .text
    org     $00006E8A
    LEA       -$40(A7),A7
    MOVEM.L   D2-D5/A2-A6,-(A7)
    PEA       ($20).W
    PEA       ($00CB7C).L
    LEA       $2C(A7),A2
    MOVE.L    A2,-(A7)
    JSR       ($0045F0).L                 ; unresolved callee
    LEA       $C(A7),A7
    MOVEQ     #0,D2
    MOVEQ     #16,D5
    LEA       ($000054).L,A4
    LEA       *-1114(PC),A5
    LEA       $44(A7),A3
    LEA       ($006E1E).L,A6
    MOVE.L    #$1892,D3
    MOVE.L    #$6B08,D4
_L0046:
    TST.W     ($016B12).L
    BNE.S     _L0092                      ; if contents of $00016B12 != 0
    MOVE.L    D5,-(A7)
    MOVE.L    D5,-(A7)
    JSR       (A4)                        ; Indirect call; target unresolved.
    ADDQ.L    #8,A7
    MOVEA.L   D0,A0
    MOVE.L    D0,D1
    ADD.L     D0,D1
    MOVE.L    D1,D0
    ADD.L     A0,D0
    LSL.L     #3,D0
    ADD.L     A0,D0
    LSL.L     #3,D0
    ASR.L     #8,D0
    MOVE.L    D0,-(A7)
    JSR       (A5)                        ; Indirect call; target unresolved.
    MOVE.L    D2,D0
    ASR.L     #2,D0
    MOVE.L    D0,-(A7)
    MOVE.L    A3,-(A7)
    MOVE.L    A2,-(A7)
    JSR       (A6)                        ; Indirect call; target unresolved.
    CLR.W     $54(A7)
    MOVE.L    A3,-(A7)
    MOVEA.L   D3,A0
    JSR       (A0)                        ; Indirect call; target unresolved.
    MOVEA.L   D4,A0
    JSR       (A0)                        ; Indirect call; target unresolved.
    SUBQ.L    #1,D5
    ADDQ.L    #3,D2
    LEA       $14(A7),A7
    TST.L     D5
    BNE.S     _L0046
_L0092:
    PEA       ($7D00).W
    CLR.L     -(A7)
    MOVE.L    ($00CBC0).L,-(A7)
    LEA       ($004690).L,A4
    JSR       (A4)                        ; Indirect call through $00004690; target unresolved.
    LEA       ($00225A).L,A2
    JSR       (A2)                        ; Indirect call through $0000225A; target unresolved.
    PEA       ($F).W
    LEA       *-1046(PC),A3
    JSR       (A3)                        ; Indirect call through $00006B26; target unresolved.
    LEA       $10(A7),A7
    MOVEQ     #12,D4
    LEA       ($000054).L,A5
    LEA       ($0000B2).L,A6              ; trap_12+2 (vector)
    MOVE.L    #$682A,D2
    MOVE.L    #$6B08,D3
_L00D6:
    TST.W     ($016B12).L
    BNE.S     _L0110                      ; if contents of $00016B12 != 0
    MOVE.L    D4,-(A7)
    MOVE.L    D4,-(A7)
    JSR       (A5)                        ; Indirect call; target unresolved.
    ADDQ.L    #8,A7
    MOVE.L    D0,D1
    ADD.L     D0,D1
    ADD.L     D1,D1
    ADD.L     D0,D1
    LSL.L     #5,D1
    PEA       ($90).W
    MOVE.L    D1,-(A7)
    JSR       (A6)                        ; Indirect call; target unresolved.
    ADDQ.L    #4,A7
    MOVE.L    D0,(A7)
    MOVEA.L   D2,A0
    JSR       (A0)                        ; Indirect call; target unresolved.
    MOVEA.L   D3,A0
    JSR       (A0)                        ; Indirect call; target unresolved.
    ADDQ.L    #4,A7
    DBRA      D4,_L00D6
    CLR.W     D4
    SUBQ.L    #1,D4
    BCC.S     _L00D6
_L0110:
    PEA       ($2).W
    LEA       *-1752(PC),A5
    JSR       (A5)                        ; Indirect call through $000068C6; target unresolved.
    ADDQ.L    #4,A7
    SUBA.L    A6,A6
    CLR.W     D2
    MOVE.L    #$B2,D3
    MOVE.L    #$6B08,D4
_L012C:
    TST.W     ($016B12).L
    BNE.S     _L016A                      ; if contents of $00016B12 != 0
    CMPI.W    #14,D2
    BNE.S     _L0142
    PEA       ($1).W
    JSR       (A5)                        ; Indirect call; target unresolved.
    ADDQ.L    #4,A7
_L0142:
    PEA       ($28).W
    MOVE.L    A6,-(A7)
    MOVEA.L   D3,A0
    JSR       (A0)                        ; Indirect call; target unresolved.
    ADDQ.L    #8,A7
    MOVEQ     #15,D1
    SUB.W     D0,D1
    MOVE.W    D1,-(A7)
    CLR.W     -(A7)
    JSR       (A3)                        ; Indirect call; target unresolved.
    MOVEA.L   D4,A0
    JSR       (A0)                        ; Indirect call; target unresolved.
    ADDQ.W    #1,D2
    LEA       $F(A6),A6
    ADDQ.L    #4,A7
    CMPI.W    #40,D2
    BNE.S     _L012C
_L016A:
    PEA       ($7D00).W
    CLR.L     -(A7)
    MOVE.L    ($00CBC0).L,-(A7)
    JSR       (A4)                        ; Indirect call; target unresolved.
    JSR       (A2)                        ; Indirect call; target unresolved.
    PEA       ($20).W
    CLR.L     -(A7)
    LEA       $58(A7),A2
    MOVE.L    A2,-(A7)
    JSR       (A4)                        ; Indirect call; target unresolved.
    MOVE.L    A2,-(A7)
    JSR       ($001892).L                 ; unresolved callee
    LEA       $1C(A7),A7
    MOVEQ     #18,D2
    LEA       *-1304(PC),A2
_L019A:
    TST.W     ($016B12).L
    BNE.S     _L01A8                      ; if contents of $00016B12 != 0
    JSR       (A2)                        ; Indirect call; target unresolved.
    SUBQ.W    #1,D2
    BNE.S     _L019A
_L01A8:
    JSR       ($0036B2).L                 ; unresolved callee
    MOVEM.L   (A7)+,D2-D5/A2-A6
    LEA       $40(A7),A7
    RTS
