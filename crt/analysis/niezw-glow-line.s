; rg-dis disassembly -- re-assemblable m68k source
; input: niezw-raw.bin
; raw binary  org: $0000682A  size: 156 bytes

    .cpu    68000
    .fpu    M68882
    .text
    org     $0000682A
    MOVEM.L   D2-D3/A2,-(A7)
    MOVE.L    $10(A7),D2
    PEA       ($500).W
    CLR.L     -(A7)
    MOVE.L    ($00CBC0).L,D0
    ADDI.L    #$3C00,D0
    MOVE.L    D0,-(A7)
    JSR       ($004690).L                 ; unresolved callee
    MOVE.W    D2,D0
    LEA       $C(A7),A7
    BGT.S     _L002C
    MOVEQ     #1,D0
_L002C:
    MOVE.W    D0,D3
    ADDI.W    #$9F,D3
    ANDI.L    #$FFFF,D3
    MOVE.W    #$A0,D2
    SUB.W     D0,D2
    ANDI.L    #$FFFF,D2
    PEA       ($1).W
    PEA       ($65).W
    MOVE.L    D3,-(A7)
    PEA       ($62).W
    MOVE.L    D2,-(A7)
    MOVE.L    ($00CBC0).L,-(A7)
    LEA       ($001EE0).L,A2
    JSR       (A2)                        ; Indirect call through $00001EE0; target unresolved.
    PEA       ($3).W
    PEA       ($64).W
    MOVE.L    D3,-(A7)
    PEA       ($63).W
    MOVE.L    D2,-(A7)
    MOVE.L    ($00CBC0).L,-(A7)
    JSR       (A2)                        ; Indirect call; target unresolved.
    LEA       $30(A7),A7
    PEA       ($67).W
    PEA       ($13F).W
    PEA       ($60).W
    CLR.L     -(A7)
    JSR       ($002180).L                 ; unresolved callee
    LEA       $10(A7),A7
    MOVEM.L   (A7)+,D2-D3/A2
    RTS
