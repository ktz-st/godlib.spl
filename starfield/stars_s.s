; Adapted from demOS FX/STARFILD by J.Hubert (2015-2022).
; MIT license: see LICENSE.demOS. GodLib / GCC ELF port, 2026.
        section text
        xdef Stars_Draw,Stars_Loop,Stars_Reset,Stars_DrawEnd
        xdef Stars_Code,Stars_CodeEnd,Stars_Erase,Stars_EraseEnd
        xdef Stars_Pix0,Stars_Pix1
        xref gStarsScreen,gStarsZ,gStarsCount,gStarsErase,gStarsEraseCount
        xref gStarsRandomX,gStarsRandomY,gStarsCurrentX,gStarsCurrentY
Stars_Draw:
        movem.l d2-d7/a2-a6,-(sp) ; GCC needs the full 32-bit callee-saved registers
        move.l  gStarsScreen,a0
        lea     gStarsZ,a1
        move.w  gStarsCount,d0
        subq.w  #1,d0
        move.l  gStarsErase,a3
        move.l  gStarsCurrentX,a4
        move.l  gStarsCurrentY,a5
        lea     Stars_Code(pc),a6
        movem.w .preload(pc),d2-d7
        bsr.s   Stars_Loop
        move.l  a4,gStarsCurrentX
        move.l  a5,gStarsCurrentY
        movem.l (sp)+,d2-d7/a2-a6
        rts
.preload: dc.w 1,4,8,32,64,128
Stars_Loop:
        move.l  (a1),a2
        addq.l  #2,(a1)+
        move.w  (a2),d1
        move.l  (a1),a2
        addq.l  #2,(a1)+
        move.w  (a2),a2
        adda.l  a0,a2
        jmp     (a6,d1.w)
Stars_Reset:
        move.l  a0,(a3)+        ; harmless erase address inside the star area
        move.l  (a4)+,d1
        bne.s   .xready
        lea     gStarsRandomX,a4
        move.l  (a4)+,d1
.xready: move.l d1,-8(a1)       ; random entries are absolute table pointers
        move.l  (a5)+,d1
        bne.s   .yready
        lea     gStarsRandomY,a5
        move.l  (a5)+,d1
.yready: move.l d1,-4(a1)
        dbra    d0,Stars_Loop
        rts
Stars_DrawEnd:
; Executable RAM, immediately after the loop: every generated DBRA must reach it.
Stars_Code:
        dcb.w   16384,0
Stars_CodeEnd:
; Pixel opcode templates, using the demOS register assignment.
Stars_Pix0:
        or.b d7,(a2)
        or.b d6,(a2)
        or.b d5,(a2)
        bset.b d3,(a2)
        or.b d4,(a2)
        or.b d3,(a2)
        bset.b d2,(a2)
        or.b d2,(a2)
Stars_Pix1:
        or.b d7,2(a2)
        or.b d6,2(a2)
        or.b d5,2(a2)
        bset.b d3,2(a2)
        or.b d4,2(a2)
        or.b d3,2(a2)
        bset.b d2,2(a2)
        or.b d2,2(a2)
Stars_Erase:
        movem.l a2-a6,-(sp)
        move.l gStarsErase,a0
        move.w gStarsEraseCount,d0 ; groups of six, minus one; caller guards zero
        moveq #0,d1
.loop:
        movem.l (a0)+,a1-a6
        movep.w d1,0(a1)
        move.b d1,4(a1)
        movep.w d1,0(a2)
        move.b d1,4(a2)
        movep.w d1,0(a3)
        move.b d1,4(a3)
        movep.w d1,0(a4)
        move.b d1,4(a4)
        movep.w d1,0(a5)
        move.b d1,4(a5)
        movep.w d1,0(a6)
        move.b d1,4(a6)
        dbra d0,.loop
        movem.l (sp)+,a2-a6
        rts
Stars_EraseEnd:
