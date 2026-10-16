        section text
        xdef Split_TimerB
        xref gSplitPanel
        xref gSplitTimerCMask
        xref gSplitReload
        xref gSplitHasBlitter

; PAL STE 320x200: 160 terrain lines, then 40 panel lines, both stride 160.
; Enter at the end of row 158; the next DE falling edge ends terrain row 159.
Split_TimerB:
        movem.l d0-d1,-(sp)
        tst.w gSplitHasBlitter
        beq.s .sync
        move.w $ffff8a3c.w,d1
        bclr #7,$ffff8a3c.w
.sync:
        move.b gSplitReload,d0
.wait_de:
        cmp.b $fffffa21.w,d0
        beq.s .wait_de
        move.b gSplitPanel+1,$ffff8205.w
        move.b gSplitPanel+2,$ffff8207.w
        move.b gSplitPanel+3,$ffff8209.w
        clr.b $fffffa1b.w
        tst.w gSplitHasBlitter
        beq.s .timer_c
        move.w d1,$ffff8a3c.w
.timer_c:
        tst.w gSplitTimerCMask
        beq.s .ack
        bset #5,$fffffa15.w
.ack:
        bclr #0,$fffffa0f.w
        movem.l (sp)+,d0-d1
        rte

        xdef Split_TimerBEnd
Split_TimerBEnd:

        section data
        even
        xdef gSplitPicture
; Palette (16 words) followed by a 320x400 four-plane image, from vscroll.
gSplitPicture:
        incbin "TOWER.BIN"
