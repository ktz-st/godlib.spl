; Ugh intro-style water: repeated/skipped rows, full-width, immutable source.
; Only water rows and the single surface line are ever written after setup.
        section text
        xdef Water_Draw,Water_DrawEnd,Water_SurfaceCopy
        xref gWaterScreen,gWaterCursor,gWaterOldCursor
        xref gWaterSurfaceCursor,gWaterOldSurface
Water_Copy macro
        movem.l 120(a0),d0-d7/a3-a4
        movem.l d0-d7/a3-a4,-(a1)
        movem.l 80(a0),d0-d7/a3-a4
        movem.l d0-d7/a3-a4,-(a1)
        movem.l 40(a0),d0-d7/a3-a4
        movem.l d0-d7/a3-a4,-(a1)
        movem.l (a0),d0-d7/a3-a4
        movem.l d0-d7/a3-a4,-(a1)
        endm
Water_Line macro
        xdef Water_CopyRow\@,Water_SkipRow\@
        move.w \1(a2),d0
        cmp.w \1(a5),d0
        beq.s Water_SkipRow\@
        lea (a6,d0.w),a0
Water_CopyRow\@:
        Water_Copy
        bra.s Water_NextRow\@
Water_SkipRow\@:
        lea -160(a1),a1
Water_NextRow\@:
        endm
Water_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l gWaterScreen,a1
        adda.l #32000,a1
        move.l gWaterCursor,a2
        move.l gWaterOldCursor,a5
        lea Water_Picture+34,a6
N       set 174
        rept 88
        Water_Line N
N       set N-2
        endr
; A1 now points just past the y=111 surface; its Y never changes.
        move.l gWaterSurfaceCursor,a0
        cmpa.l gWaterOldSurface,a0
        beq.s Water_Done
Water_SurfaceCopy:
        Water_Copy
Water_Done:
        movem.l (sp)+,d2-d7/a2-a6
        rts
Water_DrawEnd:
        section data
        even
        xdef Water_Picture,Water_Rows,Water_Surface
Water_Picture:
        incbin 'assets/CASTLE.PI1'
        even
Water_Rows:
        incbin 'assets/ROWS.BIN'
        even
Water_Surface:
        incbin 'assets/SURFACE.BIN'
        even
