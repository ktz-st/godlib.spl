; Static-source wobble: row-major preshift cache, full-colour MOVEM copy.
; Per-page history lets rows with an unchanged offset retain their pixels.
        section text
        xdef Wobble_Draw,Wobble_DrawEnd
        xref gWobbleScreen,gWobbleCursor,gWobbleOldCursor
Wobble_Line macro
        xdef Wobble_CopyRow\@,Wobble_SkipRow\@
        move.w \1(a2),d0
        cmp.w \1(a5),d0
        beq.s Wobble_SkipRow\@
        lea (a6,d0.w),a0
Wobble_CopyRow\@:
; Four 40-byte chunks, right-to-left. MOVEM predecrement leaves each chunk
; in ascending register order in RAM, so neither words nor pixels reverse.
        movem.l 120(a0),d0-d7/a3-a4
        movem.l d0-d7/a3-a4,-(a1)
        movem.l 80(a0),d0-d7/a3-a4
        movem.l d0-d7/a3-a4,-(a1)
        movem.l 40(a0),d0-d7/a3-a4
        movem.l d0-d7/a3-a4,-(a1)
        movem.l (a0),d0-d7/a3-a4
        movem.l d0-d7/a3-a4,-(a1)
        bra.s Wobble_Next\@
Wobble_SkipRow\@:
        lea -160(a1),a1
Wobble_Next\@:
        suba.w #2816,a6
        endm
Wobble_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l gWobbleScreen,a1
        adda.l #32000,a1
        move.l gWobbleCursor,a2
        move.l gWobbleOldCursor,a5
        lea Wobble_Cache+560384,a6 ; 199 * (16 preshifts * 176 bytes)
; The lookup stride and line count are fixed. Unrolling avoids two pointer
; updates, an end comparison and a branch on every copied or reused line.
N       set 0
        rept 200
        Wobble_Line N
N       set N-4
        endr
        movem.l (sp)+,d2-d7/a2-a6
        rts
Wobble_DrawEnd:
        section data
        even
        xdef Wobble_Picture,Wobble_Lookup,Wobble_Cache
Wobble_Picture:
        dc.w 0
        incbin 'assets/PALETTE.BIN'
Wobble_Lookup:
        incbin 'assets/LOOKUP.BIN'
Wobble_Cache:
        incbin 'assets/PRESHIFT.BIN'
