; Packed 352x27 one-plane conveyor. No trigonometry, no per-pixel drawing.
        section text
        xdef Scroll_Shift,Scroll_ShiftEnd,Scroll_Insert,Scroll_Draw,Scroll_DrawEnd
        xref gScrollBuffer,gScrollShift,gScrollGlyph,gScrollScreen
Scroll_Shift:
        movem.l d0-d2/a0,-(sp)
        lea gScrollBuffer,a0
        moveq #0,d1
        move.w gScrollShift,d1    ; 1..8 pixels, one pass independent of speed
        moveq #26,d2
.row:
N       set 0
        rept 21
        move.l N(a0),d0         ; current word + untouched next word
        lsl.l d1,d0
        swap d0
        move.w d0,N(a0)
N       set N+2
        endr
        move.w 42(a0),d0
        lsl.w d1,d0             ; zero-fill hidden right edge
        move.w d0,42(a0)
        lea 44(a0),a0
        dbf d2,.row
        movem.l (sp)+,d0-d2/a0
        rts
Scroll_ShiftEnd:
Scroll_Insert:
        movem.l d0/a0-a1,-(sp)
        move.l gScrollGlyph,a0
        lea gScrollBuffer+40,a1
        moveq #26,d0
.row:
        move.l (a0)+,(a1)
        lea 44(a1),a1
        dbf d0,.row
        movem.l (sp)+,d0/a0-a1
        rts
Scroll_Draw:
        movem.l d0/a0-a1,-(sp)
        lea gScrollBuffer,a0
        move.l gScrollScreen,a1
        lea 86*160(a1),a1
        moveq #26,d0
.row:
N       set 0
        rept 20
        move.w N*2(a0),N*8(a1)
N       set N+1
        endr
        lea 44(a0),a0
        lea 160(a1),a1
        dbf d0,.row
        movem.l (sp)+,d0/a0-a1
        rts
Scroll_DrawEnd:
        section data
        even
        xdef Scroll_Font
Scroll_Font:
        incbin 'assets/BUGSY.BIN'
