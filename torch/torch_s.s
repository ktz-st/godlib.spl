; Filled disk on plane 3. Erase only that plane in the old per-page bounds.
        section text
        xdef Torch_Render,Torch_RenderEnd,Torch_Clear,Torch_ClearEnd
        xdef Torch_Draw,Torch_DrawEnd
        xref gFxScreen,gFxDirty,gFxX,gFxY
Torch_Render:
        movem.l d2-d7/a2-a6,-(sp)
        bsr Torch_Clear
        bsr Torch_Draw
        movem.l (sp)+,d2-d7/a2-a6
        rts
Torch_RenderEnd:
Torch_Clear:
        move.l gFxDirty,a3
        move.w 4(a3),d6
        beq.s .done
        subq.w #1,d6
        move.l gFxScreen,a0
        adda.l (a3),a0
        move.w 6(a3),d1
        lsl.w #2,d1
        neg.w d1
        moveq #0,d0
        lea Torch_ClearWordsEnd(pc),a2
.row:
        jsr (a2,d1.w)
        lea 160(a0),a0
        dbf d6,.row
.done:
        rts
Torch_ClearWords:
X       set -160
        rept 20
        move.w d0,X(a0)
X       set X+8
        endr
Torch_ClearWordsEnd:
        rts
Torch_ClearEnd:
Torch_Draw:
        move.w gFxX,d4
        move.w gFxY,d0
        sub.w #48,d0
        lea Torch_Half,a3
        tst.w d0
        bpl.s .top
        move.w d0,d1
        neg.w d1
        add.w d1,d1
        adda.w d1,a3
        moveq #0,d0
.top:
        move.w gFxY,d6
        add.w #48,d6
        cmp.w #199,d6
        ble.s .bottom
        move.w #199,d6
.bottom:
        sub.w d0,d6
        mulu #160,d0
        move.l gFxScreen,a4
        adda.l d0,a4
        addq.l #6,a4
        lea Torch_Left(pc),a5
        lea Torch_Right(pc),a6
        lea Torch_FullEnd(pc),a2
        moveq #-1,d7
.row:
        move.w (a3)+,d0
        move.w d4,d1
        sub.w d0,d1
        bpl.s .left
        moveq #0,d1
.left:
        move.w d4,d2
        add.w d0,d2
        cmp.w #319,d2
        ble.s .right
        move.w #319,d2
.right:
        move.w d1,d0
        and.w #15,d0
        add.w d0,d0
        move.w (a5,d0.w),d3
        move.w d2,d0
        and.w #15,d0
        add.w d0,d0
        move.w (a6,d0.w),d5
        and.w #$fff0,d1
        lsr.w #1,d1
        and.w #$fff0,d2
        lsr.w #1,d2
        cmp.w d1,d2
        beq.s .single
        move.w d3,(a4,d1.w)
        lea (a4,d2.w),a0
        sub.w d2,d1
        addq.w #8,d1
        asr.w #1,d1
        jsr (a2,d1.w)
        move.w d5,(a0)
        bra.s .next
.single:
        and.w d5,d3
        move.w d3,(a4,d1.w)
.next:
        lea 160(a4),a4
        dbf d6,.row
        rts
Torch_Full:
X       set -160
        rept 20
        move.w d7,X(a0)
X       set X+8
        endr
Torch_FullEnd:
        rts
Torch_DrawEnd:
Torch_Left:
M       set $ffff
        rept 16
        dc.w M
M       set M>>1
        endr
Torch_Right:
M       set $8000
        rept 16
        dc.w M
M       set (M>>1)|$8000
        endr
        section data
        even
        xdef Torch_Image,Torch_Palette,Torch_Sine
Torch_Image:
        incbin 'assets/IMAGE.BIN'
Torch_Palette:
        incbin 'assets/PALETTE.BIN'
Torch_Half:
        incbin 'assets/HALF.BIN'
Torch_Sine:
        incbin 'assets/SINE.BIN'

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
