        section text
        xdef Original_Reflect
Original_Reflect:
        movem.l d2-d7/a2-a6,-(sp)
        move.l a0,-(sp)
        move.l 14(a0),Original_Code+$cc
        move.w 8(a0),d0
        move.w 10(a0),d1
        move.w 12(a0),d2
        move.l 4(a0),a1
        move.l (a0),a0
        jsr Original_Code
        move.l (sp)+,a0
        move.l Original_Code+$cc,14(a0)
        movem.l (sp)+,d2-d7/a2-a6
        rts
Original_Code:
        incbin 'analysis/original-core.bin'
        even
