; rg-dis disassembly -- re-assemblable m68k source
; input: niezw-raw.bin
; raw binary  org: $00006A5C  size: 172 bytes

    .cpu    68000
    .fpu    M68882
    .text
    org     $00006A5C
    MOVEM.L   D2-D7/A2-A6,-(A7)
    MOVE.L    $30(A7),D3
    MOVE.W    D3,D6
    MOVEA.W   D3,A2
    MOVE.L    A2,D2
    BPL.S     _L0012
    ADDQ.L    #1,D2
_L0012:
    ASR.L     #1,D2
    NEG.L     D2
    ASR.W     #1,D3
    MOVEA.W   #$FF9C,A6
    MOVEQ     #0,D4
    MOVE.L    #$FFFFB1E0,D5
    LEA       ($0000B2).L,A4              ; trap_12+2 (vector)
    LEA       *-234(PC),A5
    MOVE.W    #$C7,D7
_L0032:
    MOVEA.L   ($00CBC0).L,A3
    TST.W     D6
    BEQ.S     _L0096
    CMPA.L    D2,A6
    BLT.S     _L0096
    MOVE.W    A6,D0
    CMP.W     D3,D0
    BGE.S     _L0096
    MOVE.L    A2,-(A7)
    MOVE.L    D5,-(A7)
    JSR       (A4)                        ; Indirect call; target unresolved.
    ADDQ.L    #8,A7
    ADDI.W    #100,D0
    CMPI.W    #$C7,D0
    BLE.S     _L008E
    MOVE.W    D7,D0
_L005A:
    MOVEA.W   D0,A0
    MOVE.L    A0,-(A7)
    MOVE.L    ($00CBBC).L,-(A7)
    PEA       $64(A6)
    MOVE.L    A3,-(A7)
    JSR       (A5)                        ; Indirect call; target unresolved.
    LEA       $10(A7),A7
_L0070:
    ADDI.L    #$C8,D5
    ADDI.L    #$A0,D4
    ADDQ.L    #1,A6
    MOVEQ     #100,D0
    CMP.L     A6,D0
    BNE.S     _L0032
    MOVEM.L   (A7)+,D2-D7/A2-A6
    JMP       ($00225A).L                 ; unresolved callee
_L008E:
    TST.W     D0
    BGE.S     _L005A
    CLR.W     D0
    BRA.S     _L005A
_L0096:
    PEA       ($A0).W
    CLR.L     -(A7)
    PEA       (A3,D4.L)
    JSR       ($004690).L                 ; unresolved callee
    LEA       $C(A7),A7
    BRA.S     _L0070
