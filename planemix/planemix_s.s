; SMFX indecision.128 inspired: independent cyclic bit patterns per plane.
; Two cells sizes (16 and 8 px). Palette resolves intersections automatically.
        section text
        xdef PlaneMix_Draw,PlaneMix_DrawEnd
        xref gFxScreen,gFxAX,gFxAY,gFxBX,gFxBY
PlaneMix_Draw:
        movem.l d2-d7,-(sp)
        move.l gFxScreen,a0
        lea 40*160(a0),a0
        move.l #$ffff0000,d0
        move.w gFxAX,d2
        rol.l d2,d0
        swap d0
        move.w #$ff00,d1
        move.w gFxBX,d2
        rol.w d2,d1
        move.w gFxAY,d5
        btst #4,d5
        beq.s .a
        not.l d0
.a:
        and.w #15,d5
        move.w gFxBY,d6
        btst #3,d6
        beq.s .b
        not.w d1
.b:
        and.w #7,d6
        move.w d0,d2
        swap d2
        move.w d1,d2
        swap d0
        move.w d0,d3
        swap d3
        move.w d1,d3
        move.l #$ffff0000,d4
        moveq #127,d7
.row:
X       set 0
        rept 10
        move.l d2,X(a0)
        move.l d3,X+8(a0)
X       set X+16
        endr
        lea 160(a0),a0
        addq.w #1,d5
        cmp.w #16,d5
        bne.s .keepa
        clr.w d5
        eor.l d4,d2
        eor.l d4,d3
.keepa:
        addq.w #1,d6
        and.w #7,d6
        bne.s .keepb
        not.w d2
        not.w d3
.keepb:
        dbf d7,.row
        movem.l (sp)+,d2-d7
        rts
PlaneMix_DrawEnd:

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
