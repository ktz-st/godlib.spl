; Original span renderer for a rotated, zoomed checkerboard. Plain 68000.
; Commands contain fill-code offsets and partial-word XOR masks. No pixel loop or C rasterizer.
        section text
        xdef Checker_Draw,Checker_DrawEnd
        xref gCheckerScreen,gCheckerCommands
Checker_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l gCheckerScreen,a6
        lea 56*160(a6),a6
        move.l gCheckerCommands,a1
        lea Checker_FillEnd(pc),a3
        moveq #95,d7
.row:
        move.l a6,a0
        move.w (a1)+,d4
        move.w d4,d5
.edge:
        move.w (a1)+,d0
        bgt.s .last
        beq.s .toggle
        move.w d5,(a0)
        addq.l #8,a0
        addq.w #4,d0
        jsr (a3,d0.w)
        move.w d4,d5
.toggle:
        move.w (a1)+,d2
        eor.w d2,d5
        not.w d4
        bra.s .edge
.last:
        addq.l #2,a1
        move.w d5,(a0)
        addq.l #8,a0
        lea 160(a6),a6
        move.l a0,d0
        sub.l a6,d0
        asr.w #1,d0
        jsr (a3,d0.w)
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
        section data
        even
        xdef Checker_Spans,Checker_Offsets
Checker_Spans:
        incbin 'assets/SPANS.BIN'
Checker_Offsets:
        incbin 'assets/OFFSETS.BIN'
        section text
        xdef Tiny_RasterSync,Tiny_RasterSyncEnd
Tiny_RasterSync:
        movem.l d0-d1/a1,-(sp)
        move.l a0,d0
        lsr.l #8,d0
        add.w #5,d0
        lea $ffff8205.w,a1
.wait:
        movep.w 0(a1),d1
        cmp.w d0,d1
        bne.s .wait
        movem.l (sp)+,d0-d1/a1
        rts
Tiny_RasterSyncEnd:
