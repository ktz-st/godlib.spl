        section text
        xdef Lens_Init,Lens_InitEnd,Lens_Render,Lens_RenderEnd
        xdef Lens_Clear,Lens_ClearEnd,Lens_Draw,Lens_DrawEnd
        xref gFxScreen,gFxBackground,gFxDirty,gFxX,gFxY
; Convert the clean planar background once to three shifted colour-index arrays.
Lens_Init:
        movem.l d2-d7/a2-a3,-(sp)
        move.l gFxBackground,a0
        lea Lens_Src0,a1
        lea Lens_Src1,a2
        lea Lens_Src2,a3
        move.w #3999,d7
.block:
        movem.w (a0)+,d0-d3
        rept 16
        add.w d3,d3
        addx.w d4,d4
        add.w d2,d2
        addx.w d4,d4
        add.w d1,d1
        addx.w d4,d4
        add.w d0,d0
        addx.w d4,d4
        and.w #15,d4
        lsl.w #2,d4
        move.w d4,(a1)+
        lsl.w #4,d4
        move.w d4,(a2)+
        lsl.w #4,d4
        move.w d4,(a3)+
        endr
        dbf d7,.block
        movem.l (sp)+,d2-d7/a2-a3
        rts
Lens_InitEnd:
Lens_Render:
        movem.l d2-d7/a2-a6,-(sp)
        bsr Lens_Clear
        bsr Lens_Draw
        movem.l (sp)+,d2-d7/a2-a6
        rts
Lens_RenderEnd:
Lens_Clear:
        move.l gFxDirty,a5
        move.w 4(a5),d7
        beq.s .done
        subq.w #1,d7
        move.l (a5),d0
        move.l gFxBackground,a1
        adda.l d0,a1
        move.l gFxScreen,a0
        adda.l d0,a0
        cmp.w #4,6(a5)
        beq.s .four
.five:
        movem.l (a1)+,d0-d6/a2-a4
        movem.l d0-d6/a2-a4,(a0)
        lea 120(a1),a1
        lea 160(a0),a0
        dbf d7,.five
        rts
.four:
        movem.l (a1)+,d0-d6/a2
        movem.l d0-d6/a2,(a0)
        lea 128(a1),a1
        lea 160(a0),a0
        dbf d7,.four
.done:
        rts
Lens_ClearEnd:
Lens_Draw:
        moveq #0,d0
        move.w gFxX,d0
        move.w d0,d7
        and.w #8,d7
        move.w d0,d1
        and.w #7,d1
        lsl.w #2,d1
        move.l Lens_Kernels(pc,d1.w),d6
        move.w gFxY,d1
        mulu #640,d1
        add.w d0,d0
        add.l d0,d1
        lea Lens_Src0,a2
        adda.l d1,a2
        lea Lens_Src1,a3
        adda.l d1,a3
        lea Lens_Src2,a4
        adda.l d1,a4
        move.w gFxY,d1
        mulu #160,d1
        move.w gFxX,d0
        move.w d0,d2
        lsr.w #4,d0
        lsl.w #3,d0
        lsr.w #3,d2
        and.w #1,d2
        add.w d2,d0
        add.l d0,d1
        move.l gFxScreen,a0
        adda.l d1,a0
        lea Lens_LUT0,a5
        lea Lens_LUT1,a6
        lea Lens_LUT2,a1
        move.l d6,-(sp)
        rts
Lens_Kernels:
        dc.l Lens_K0,Lens_K1,Lens_K2,Lens_K3,Lens_K4,Lens_K5,Lens_K6,Lens_K7
        include 'assets/kernel.inc'
Lens_DrawEnd:
        section data
        even
        xdef Lens_Image,Lens_Palette,Lens_Sine
Lens_Image: incbin 'assets/IMAGE.BIN'
Lens_Palette: incbin 'assets/PALETTE.BIN'
Lens_Sine: incbin 'assets/SINE.BIN'
Lens_LUT0: incbin 'assets/LUT0.BIN'
Lens_LUT1: incbin 'assets/LUT1.BIN'
Lens_LUT2: incbin 'assets/LUT2.BIN'
        section bss,bss
        even
Lens_Src0: ds.w 64000
Lens_Src1: ds.w 64000
Lens_Src2: ds.w 64000

        section text
        xdef Fx_RasterSync,Fx_RasterSyncEnd
Fx_RasterSync:
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
Fx_RasterSyncEnd:
