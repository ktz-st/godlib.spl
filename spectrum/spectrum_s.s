; Spectrum 512/4096 display kernel adapted from Dead Hackers Society
; stsys10/spec512/spec512.s and sys/common.s, September 2011 (ae / DHS).
; 199 copies of the 512-cycle scanline. First visible line is sacrificed.
        section text
        xdef Spectrum_TimerA,Spectrum_TimerAEnd,Spectrum_Hbl
        xdef Spectrum_Code,Spectrum_CodeEnd
        xdef Spectrum_Pixels,Spectrum_PalST,Spectrum_PalSTE
        xref gSpectrumFramePal,gSpectrumTimerCMask,gSpectrumRasterFrames
Spectrum_Hbl:
        rte
Spectrum_TimerA:
        movem.l d0-d7/a0-a6,-(sp)
; Same hard synchronization as stsys10. The VBL arms this before visible video.
        move.w #$2100,sr
        stop #$2100
        move.w #$2700,sr
        clr.b $fffffa19.w
        lea $ffff8209.w,a0
        moveq #127,d1
.sync: tst.b (a0)
        beq.s .sync
        move.b (a0),d2
        sub.b d2,d1
        lsr.l d1,d1
; Original preamble: 35 NOP + LEA abs.l (12 cycles). The palette pointer is
; selected per VBL, so use 33 NOP + MOVE abs.l (20 cycles): identical timing.
        dcb.w 33,$4e71
        move.l gSpectrumFramePal,a0
        lea $ffff8240.w,a1
        move.l a1,a2
        jsr Spectrum_Code
        addq.l #1,gSpectrumRasterFrames
        bclr #5,$fffffa0f.w
        tst.w gSpectrumTimerCMask
        beq.s .done
        bset #5,$fffffa15.w
.done:  movem.l (sp)+,d0-d7/a0-a6
        rte
Spectrum_TimerAEnd:
Spectrum_Code:
        rept 199
        rept 8
        move.l (a0)+,(a2)+       ; 160 cycles: palette 1
        endr
        dcb.w 5,$4e71           ; 20 cycles
        move.l a1,a2            ; 12 cycles: reset all three write cursors
        move.l a1,a3
        move.l a1,a4
        rept 8
        move.l (a0)+,(a3)+       ; 160 cycles: palette 2
        endr
        rept 8
        move.l (a0)+,(a4)+       ; 160 cycles: palette 3
        endr
        endr
        rts
Spectrum_CodeEnd:
        section data
Spectrum_Pixels:
        ifd SPECTRUM_CHART
        incbin 'assets/CHARTPIX.BIN'
        else
        incbin 'assets/PIXELS.BIN'
        endc
        even
Spectrum_PalST:
        ifd SPECTRUM_CHART
        incbin 'assets/CHARTST.BIN'
        else
        incbin 'assets/PALST.BIN'
        endc
        even
Spectrum_PalSTE:
        ifd SPECTRUM_CHART
        incbin 'assets/CHARTSTE.BIN'
        else
        incbin 'assets/PALSTE.BIN'
        endc
        even
