        section text
        xdef HSplit_SetHud
        xdef HSplit_TimerB
        xdef HSplit_TimerBEnd
        xref gHSplitHudEnd
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

; Like PacMad, enter two lines early (Timer B=14). Wait for the actual
; end of the 16-row aligned HUD, not an earlier low-byte wrap.
HSplit_TimerB:
        movem.l d0-d7,-(sp)
        clr.b $fffffa1b.w
        tst.w gHSplitHasBlitter
        beq.s .prepare
        move.w $ffff8a3c.w,d7
        bclr #7,$ffff8a3c.w
.prepare:
        move.b gHSplitTerrain+1,d4
        move.b gHSplitTerrain+2,d3
        move.b gHSplitTerrain+3,d2
        move.b gHSplitFine+1,d5
        move.b gHSplitLineWords+1,d6
        move.b gHSplitHudEnd+2,d1
.wait:
        move.b $ffff8207.w,d0
        cmp.b d1,d0
        bne.s .wait
        tst.b $ffff8209.w
        bne.s .wait
; All five writes must finish before the next line fetch. Preloaded registers
; keep the three address bytes plus fine scroll and line skip within blank.
        move.b d4,$ffff8205.w
        move.b d3,$ffff8207.w
        move.b d2,$ffff8209.w
        move.b d5,$ffff8265.w
        move.b d6,$ffff820f.w
        tst.w gHSplitHasBlitter
        beq.s .timer_c
        move.w d7,$ffff8a3c.w
.timer_c:
        tst.w gHSplitTimerCMask
        beq.s .ack
        bset #5,$fffffa15.w
.ack:
        bclr #0,$fffffa0f.w
        movem.l (sp)+,d0-d7
        rte
HSplit_TimerBEnd:

        section data
        even
        xdef gHSplitPicture
; Same 640x200 ST-palette panorama as ../hscroll, embedded in the executable.
gHSplitPicture:
        incbin "PANORAMA.BIN"
