; Original DCK TAPIS bitmap and palette records, temporal VBL adaptation.
; GodLib callback (RTS), not an interrupt owner (RTE). Only volatile ABI regs
; d0/d1/a0 are touched; in particular the VBL iterator d7/a6 is preserved.
        section text
        xdef Tp_Vbl,Tp_VblEnd,Tp_Write,Tp_WriteEnd,Tp_Show,Tp_ShowEnd
        xdef Tp_Period
        xref gTpControl,gTpLatched,gTpPhase,gTpCountdown,gTpTicks,gTpChanges,gTpDest
Tp_Vbl:
        addq.l #1,gTpTicks
        move.w gTpControl,d0       ; one atomic command snapshot per VBL
        move.w gTpLatched,d1
        move.w d0,gTpLatched
        eor.w d0,d1
        btst #4,d1                 ; manual step is an edge-toggle command
        bne.s .advance
        andi.w #12,d1
        beq.s .sameperiod
        bsr.w Tp_Period
.sameperiod:
        btst #0,d0
        bne.s Tp_Write
        subq.w #1,gTpCountdown
        bne.s Tp_Write
.advance:
        bsr.w Tp_Period
        move.w gTpPhase,d1
        btst #1,d0
        bne.s .reverse
        addq.w #1,d1
        cmpi.w #14,d1
        blo.s .phase
        moveq #0,d1
        bra.s .phase
.reverse:
        subq.w #1,d1
        bpl.s .phase
        moveq #13,d1
.phase:
        move.w d1,gTpPhase
        addq.l #1,gTpChanges
Tp_Write:
        move.w gTpPhase,d0
        lsl.w #5,d0
        lea Tp_Palettes,a0
        adda.w d0,a0
        move.l (a0)+,$ffff8240.w
        move.l (a0)+,$ffff8244.w
        move.l (a0)+,$ffff8248.w
        move.l (a0)+,$ffff824c.w
        move.l (a0)+,$ffff8250.w
        move.l (a0)+,$ffff8254.w
        move.l (a0)+,$ffff8258.w
        move.l (a0)+,$ffff825c.w
        rts
Tp_WriteEnd:
Tp_Period:
        move.w d0,d1
        lsr.w #2,d1
        andi.w #3,d1
        add.w d1,d1
        lea Tp_Periods,a0
        move.w 0(a0,d1.w),gTpCountdown
        rts
Tp_VblEnd:
Tp_Show:
        lea Tp_Picture,a0
        move.l gTpDest,a1
        move.w #199,d0
.row:
        rept 40
        move.l (a0)+,(a1)+
        endr
        dbf d0,.row
        rts
Tp_ShowEnd:
        section data
        even
        xdef Tp_Picture,Tp_Palettes
Tp_Periods: dc.w 1,2,4,4
Tp_Palettes: incbin "assets/PALETTES.BIN"
Tp_Picture: incbin "assets/PICTURE.BIN"
