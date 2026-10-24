; DCK XOR starfield: four cardinal directions, six-byte x/y/speed records.
; GodLib adaptation: separate saved XOR lists for both display pages.
        section text
        xdef Xor_Init,Xor_Advance,Xor_Erase,Xor_Draw,Xor_RuntimeEnd
        xref gXorStars,gXorCount,gXorMode,gXorScreen,gXorSaved,gXorOldCount
Xor_Init:
        movem.l d0-d7/a0-a6,-(sp)
        lea gXorStars,a0
        move.w #$ace1,d7
        move.w #255,d6
.star:
        bsr.s .random
        andi.l #$ffff,d0
        divu.w #320,d0
        swap d0
        move.w d0,(a0)+
        bsr.s .random
        andi.l #$ffff,d0
        divu.w #144,d0
        swap d0
        addi.w #28,d0
        move.w d0,(a0)+
        bsr.s .random
        andi.w #3,d0
        addq.w #1,d0
        move.w d0,(a0)+
        dbf d6,.star
        movem.l (sp)+,d0-d7/a0-a6
        rts
.random:
        lsr.w #1,d7
        bcc.s .noeor
        eori.w #$b400,d7
.noeor:
        moveq #0,d0
        move.w d7,d0
        rts
Xor_Advance:
        movem.l d0-d7/a0-a6,-(sp)
        lea gXorStars,a0
        move.w gXorCount,d7
        subq.w #1,d7
        move.w gXorMode,d0
        lsl.w #2,d0
        lea .modes(pc),a1
        move.l 0(a1,d0.w),a1
        jmp (a1)
.modes: dc.l .right,.left,.down,.up
.right:
        move.w (a0),d0
        add.w 4(a0),d0
        cmpi.w #320,d0
        blo.s .rfit
        subi.w #320,d0
.rfit:  move.w d0,(a0)
        lea 6(a0),a0
        dbf d7,.right
        bra.s .done
.left:
        move.w (a0),d0
        sub.w 4(a0),d0
        bpl.s .lfit
        addi.w #320,d0
.lfit:  move.w d0,(a0)
        lea 6(a0),a0
        dbf d7,.left
        bra.s .done
.down:
        move.w 2(a0),d0
        add.w 4(a0),d0
        cmpi.w #172,d0
        blo.s .dfit
        subi.w #144,d0
.dfit:  move.w d0,2(a0)
        lea 6(a0),a0
        dbf d7,.down
        bra.s .done
.up:
        move.w 2(a0),d0
        sub.w 4(a0),d0
        cmpi.w #28,d0
        bge.s .ufit
        addi.w #144,d0
.ufit:  move.w d0,2(a0)
        lea 6(a0),a0
        dbf d7,.up
.done:
        movem.l (sp)+,d0-d7/a0-a6
        rts
Xor_Erase:
        movem.l d0-d7/a0-a6,-(sp)
        move.w gXorOldCount,d7
        beq.s .done
        subq.w #1,d7
        move.l gXorSaved,a0
        move.l gXorScreen,a1
        addq.l #2,a1
.loop:
        move.w (a0)+,d0
        move.w (a0)+,d1
        eor.w d1,0(a1,d0.w)
        dbf d7,.loop
.done:
        movem.l (sp)+,d0-d7/a0-a6
        rts
Xor_Draw:
        movem.l d0-d7/a0-a6,-(sp)
        lea gXorStars,a0
        move.l gXorScreen,a1
        addq.l #2,a1
        move.l gXorSaved,a2
        lea Xor_Masks(pc),a3
        lea Xor_Rows(pc),a4
        move.w gXorCount,d7
        subq.w #1,d7
.loop:
        move.w (a0),d0
        move.w d0,d1
        andi.w #15,d1
        add.w d1,d1
        move.w 0(a3,d1.w),d3
        lsr.w #1,d0
        andi.w #$fff8,d0
        move.w 2(a0),d2
        add.w d2,d2
        add.w 0(a4,d2.w),d0
        move.w d0,(a2)+
        move.w d3,(a2)+
        eor.w d3,0(a1,d0.w)
        lea 6(a0),a0
        dbf d7,.loop
        movem.l (sp)+,d0-d7/a0-a6
        rts
Xor_RuntimeEnd:
Xor_Masks: dc.w $8000,$4000,$2000,$1000,$800,$400,$200,$100,$80,$40,$20,$10,8,4,2,1
Xor_Rows:
Y       set 0
        rept 200
        dc.w Y*160
Y       set Y+1
        endr
