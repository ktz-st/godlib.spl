; Example-local port of SuperHex's hspan_asm: bitplane 3, interleaved ST-low.
; Inclusive endpoints, word edge masks, whole-word stores in the interior.
; Does not touch planes 0..2. GCC ELF fastcall, preserve callee-save registers.
        section text
        xdef Iris_Fill,Iris_FillEnd
Iris_Fill:
        movem.l d2-d7/a2-a3,-(sp)
        lea 6(a0),a2
        move.w #199,d7
        moveq #-1,d6
.row:
        move.w (a1)+,d0
        move.w (a1)+,d1
        cmp.w d0,d1
        blt.s .next
        move.w d0,d2
        and.w #15,d2
        move.w d6,d3
        lsr.w d2,d3              ; left inclusive mask
        move.w d1,d2
        and.w #15,d2
        move.w #15,d4
        sub.w d2,d4
        move.w d6,d5
        lsl.w d4,d5              ; right inclusive mask
        lsr.w #4,d0
        lsr.w #4,d1
        sub.w d0,d1              ; difference in word columns
        lsl.w #3,d0
        lea (a2,d0.w),a3
        tst.w d1
        bne.s .many
        and.w d5,d3
        or.w d3,(a3)
        bra.s .next
.many:
        or.w d3,(a3)
        addq.l #8,a3
        subq.w #2,d1             ; middle words - 1
        bmi.s .right
.middle:
        move.w d6,(a3)
        addq.l #8,a3
        dbra d1,.middle
.right:
        or.w d5,(a3)
.next:
        lea 160(a2),a2
        dbra d7,.row
        movem.l (sp)+,d2-d7/a2-a3
        rts
Iris_FillEnd:
        section data
        even
        xdef Iris_Image,Iris_Image2,Iris_Palette,Iris_Palette2,Iris_Sine
Iris_Image: incbin 'assets/IMAGE.BIN'
Iris_Image2: incbin 'assets/IMAGE2.BIN'
Iris_Palette: incbin 'assets/PALETTE.BIN'
Iris_Palette2: incbin 'assets/PALETTE2.BIN'
Iris_Sine:
        include 'assets/SINE.S'
