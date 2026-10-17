; Software four-plane horizontal wobble. No blitter or STE registers.
        section text
        xdef Wobble_Draw,Wobble_DrawEnd
        xref gWobbleScreen,gWobbleCommands
Wobble_Draw:
        movem.l d0-d7/a0-a4,-(sp)
        lea Wobble_Planes,a0
        move.l gWobbleScreen,a1
        lea gWobbleCommands,a2
        move.w #199,d7
.row:
        move.w (a2)+,d0         ; coarse source offset (0,2,4 bytes)
        lea (a0,d0.w),a3
        move.w (a2)+,d1         ; fine shift, always <=8
        move.w (a2)+,d2         ; 0 copy / 1 left+swap / 2 right
        move.l a1,a4
        moveq #3,d6
        tst.w d2
        beq .copy
        subq.w #1,d2
        bne .right
.left:
N       set 0
        rept 20
        move.l N*2(a3),d0
        lsl.l d1,d0
        swap d0
        move.w d0,N*8(a4)
N       set N+1
        endr
        lea 8800(a3),a3
        addq.l #2,a4
        dbf d6,.left
        bra .next
.right:
N       set 0
        rept 20
        move.l N*2(a3),d0
        lsr.l d1,d0
        move.w d0,N*8(a4)
N       set N+1
        endr
        lea 8800(a3),a3
        addq.l #2,a4
        dbf d6,.right
        bra .next
.copy:
N       set 0
        rept 20
        move.w N*2(a3),N*8(a4)
N       set N+1
        endr
        lea 8800(a3),a3
        addq.l #2,a4
        dbf d6,.copy
.next:
        lea 44(a0),a0
        lea 160(a1),a1
        dbf d7,.row
        movem.l (sp)+,d0-d7/a0-a4
        rts
Wobble_DrawEnd:
        section data
        even
        xdef Wobble_Picture,Wobble_Planes
Wobble_Picture:
        incbin 'assets/COAST.PI1'
        even
Wobble_Planes:
        incbin 'assets/PLANES.BIN'
