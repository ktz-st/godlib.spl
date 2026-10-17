; Original span renderer for a rotated, zoomed checkerboard. Plain 68000.
; Commands contain sorted transition X positions. No pixel loop or C rasterizer.
        section text
        xdef Checker_Draw,Checker_DrawEnd
        xref gCheckerScreen,gCheckerRows
Checker_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l gCheckerScreen,a6
        lea 48*160(a6),a6
        lea gCheckerRows,a1
        lea Checker_Masks(pc),a2
        lea Checker_FillEnd(pc),a3
        moveq #111,d7
.row:
        move.l a6,a0
        move.w (a1)+,d4
        move.w d4,d5
        lea 46(a1),a5
.edge:
        moveq #0,d0
        move.w (a1)+,d0
        move.w d0,d2
        move.w d0,d1
        and.w #15,d1
        add.w d1,d1
        lsr.w #4,d0
        lsl.w #3,d0
        lea (a6,d0.w),a4
        cmpa.l a0,a4
        beq.s .toggle
        move.w d5,(a0)
        addq.l #8,a0
        move.l a4,d0
        sub.l a0,d0
        neg.w d0
        asr.w #1,d0
        jsr (a3,d0.w)
        move.w d4,d5
.toggle:
        cmp.w #320,d2
        beq.s .next
        move.w (a2,d1.w),d3
        eor.w d3,d5
        not.w d4
        bra.s .edge
.next:
        move.l a5,a1
        lea 160(a6),a6
        dbf d7,.row
        movem.l (sp)+,d2-d7/a2-a6
        rts
; Four code bytes per complete word: jump over the unused prefix.
Checker_Fill:
        rept 20
        move.w d4,(a0)
        addq.l #8,a0
        endr
Checker_FillEnd:
        rts
Checker_DrawEnd:
Checker_Masks:
M       set $ffff
        rept 16
        dc.w M
M       set M>>1
        endr
        section data
        even
        xdef Checker_Params
Checker_Params:
        incbin 'assets/PARAMS.BIN'

        section text
        xdef Tiny_RasterSync,Tiny_RasterSyncEnd
Tiny_RasterSync:
        movem.l d0-d1/a1,-(sp)
        move.l a0,d0
        lsr.l #8,d0
        add.w #20,d0
        lea $ffff8205.w,a1
.wait:
        movep.w 0(a1),d1
        cmp.w d0,d1
        bne.s .wait
        movem.l (sp)+,d0-d1/a1
        rts
Tiny_RasterSyncEnd:
