        section text
        xdef HSplit_SetHud
        xdef HSplit_TimerB
        xdef HSplit_TimerBEnd
        xref gHSplitTerrain
        xref gHSplitFine
        xref gHSplitLineWords
        xref gHSplitTimerCMask
        xref gHSplitHasBlitter

; VBL only, A0=aligned HUD. HUD uses stride 160, fine X=0.
HSplit_SetHud:
        clr.b $ffff8265.w
        clr.b $ffff820f.w
        move.l a0,d0
        move.b d0,$ffff820d.w
        move.b d0,$ffff8209.w
        lsr.l #8,d0
        move.b d0,$ffff8203.w
        move.b d0,$ffff8207.w
        lsr.l #8,d0
        move.b d0,$ffff8201.w
        move.b d0,$ffff8205.w
        rts

; Enter two lines early (Timer B=14). Preload all values, including the full
; terrain palette, before synchronizing to the second following DE edge.
HSplit_TimerB:
        movem.l d0-d7/a0-a6,-(sp)
        tst.w gHSplitHasBlitter
        beq.s .prepare
; Hold the blitter mode in D4's high word; its low byte becomes the DE count.
        move.w $ffff8a3c.w,d4
        swap d4
        bclr #7,$ffff8a3c.w
.prepare:
        move.l gHSplitTerrain,d0
        move.b gHSplitTerrain+1,d1
        move.b gHSplitFine+1,d2
        move.b gHSplitLineWords+1,d3
; D5-D7 and A0-A4 hold the eight palette longwords; A5/A6 stay usable pointers.
        movem.l gHSplitPicture,d5-d7/a0-a4
        movea.w #$fa21,a5
        movea.w #$8240,a6
        move.b #12,d4
.wait_de:
        cmp.b (a5),d4
        bne.s .wait_de
; MOVEP.W writes the middle and low address bytes at 8207/8209 in 16 cycles.
; All address/stride writes finish in the right border. Palette stores can
; continue through the next left border, before its first visible pixel.
        move.b d1,$ffff8205.w
        movep.w d0,-57(a6)
        move.b d2,$ffff8265.w
        move.b d3,$ffff820f.w
        movem.l d5-d7/a0-a4,(a6)
        clr.b $fffffa1b.w
        tst.w gHSplitHasBlitter
        beq.s .timer_c
        swap d4
        move.w d4,$ffff8a3c.w
.timer_c:
        tst.w gHSplitTimerCMask
        beq.s .ack
        bset #5,$fffffa15.w
.ack:
        bclr #0,$fffffa0f.w
        movem.l (sp)+,d0-d7/a0-a6
        rte
HSplit_TimerBEnd:

        section data
        even
        xdef gHSplitPicture
; Same 640x200 STE-palette panorama as ../hscroll, embedded in the executable.
gHSplitPicture:
        incbin "PANORAMA.BIN"
