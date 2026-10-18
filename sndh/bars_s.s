; STF_DEMO V1.0 (C) 1993 James Boulton: original 16x150 four-plane VU graphics.
; Adapted to vasm/GCC fastcall, three PSG channels A/B/C and minimal row updates.
; No direct PSG reads: PSG snapshot supplies 0..16 volume levels.
        section text
        xdef PsgBars_Draw,PsgBars_DrawEnd
; a0 = screen, a1 = U16 levels[3], 4(sp) = U16 previousLevels[3] for this page.
; All levels must be 0..16. Previous levels begin at zero on cleared screens.
PsgBars_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l 48(sp),a2
        lea 32*160(a0),a3
        lea PsgBars_xOffsets(pc),a4
        moveq #2,d7
.channel:
        move.w (a4)+,d5
        moveq #0,d0
        move.w (a1)+,d0
        moveq #0,d1
        move.w (a2),d1
        cmp.w d0,d1
        beq .next
        move.w d0,(a2)+
; Transition table: 17 rows * 17 records * 6 bytes, indexed without MULU/DIVU.
        move.w d0,d2
        add.w d2,d2
        lea PsgBars_spanRows(pc),a6
        move.w (a6,d2.w),d2
        move.w d1,d3
        lsl.w #1,d1
        lsl.w #2,d3
        add.w d3,d1
        add.w d1,d2
        lea PsgBars_spans,a6
        adda.w d2,a6
        moveq #0,d2
        move.w (a6)+,d2     ; destination first-row byte offset
        move.w (a6)+,d3     ; source first-row byte offset
        move.w (a6),d6      ; number of rows
        beq.s .advance
        move.l a3,a0
        adda.w d5,a0
        adda.l d2,a0
        add.w d0,d0
        lea PsgBars_frameOffsets(pc),a6
        move.w (a6,d0.w),d0
        lea PsgBars_frames,a5
        adda.w d0,a5
        adda.w d3,a5
        subq.w #1,d6
.row:
        move.l (a5)+,d2
        move.l (a5)+,d3
        movep.l d2,1(a0)
        movep.l d3,8(a0)
        lea 160(a0),a0
        dbf d6,.row
.advance:
        dbf d7,.channel
        movem.l (sp)+,d2-d7/a2-a6
        rts
.next:
        addq.l #2,a2
        bra.s .advance
PsgBars_DrawEnd:
; Three 16px bars at X=120/152/184, with 16px gaps; offsets below
; address the preceding 16px group and MOVEP applies the +8px phase.
PsgBars_xOffsets:
        dc.w 56,72,88
PsgBars_frameOffsets:
N       set 0
        rept 17
        dc.w N*1200
N       set N+1
        endr
PsgBars_spanRows:
N       set 0
        rept 17
        dc.w N*17*6
N       set N+1
        endr
        section data
        even
        xdef gPsgBarsPalette
 gPsgBarsPalette:
        incbin 'assets/PALETTE.BIN'
PsgBars_frames:
        incbin 'assets/FRAMES8.BIN'
PsgBars_spans:
        incbin 'assets/SPANS.BIN'
