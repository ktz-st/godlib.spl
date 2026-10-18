; SuperHex bg_copy, 320x200, plane 2. GCC ELF fastcall:
; a0 packed source (8000 B), a1 four-plane destination, d0 inverse 0/1.
; Does not touch planes 0, 1 or 3. Runtime rendering is entirely ASM.
        section text
        xdef Wedges_Copy,Wedges_CopyEnd
        xref gWedgesBlitter
Wedges_Copy:
        adda.w #4,a1
        tst.w gWedgesBlitter
        bne .blitter
        move.w #199,d1
        tst.w d0
        bne.s .inverse
.normal:
        rept 20
        move.w (a0)+,REPTN*8(a1)
        endr
        lea 160(a1),a1
        dbra d1,.normal
        rts
.inverse:
        rept 20
        move.w (a0)+,d0
        not.w d0
        move.w d0,REPTN*8(a1)
        endr
        lea 160(a1),a1
        dbra d1,.inverse
        rts
.blitter:
        move.l a2,-(sp)
        movea.w #$8a00,a2
.wait:
        btst #7,$3c(a2)
        bne.s .wait
        move.l #$00020002,$20(a2) ; packed source, x/y increment 2
        move.l a0,$24(a2)
        move.l #-1,$28(a2)
        move.w #-1,$2c(a2)
        move.l #$00080008,$2e(a2) ; destination x/y increment 8
        move.l a1,$32(a2)
        move.l #$001400c8,$36(a2) ; 20 words x 200 rows
        move.b #2,$3a(a2)        ; HOP = source
        move.b #3,$3b(a2)        ; copy
        tst.w d0
        beq.s .copy
        move.b #12,$3b(a2)       ; NOT source
.copy:
        clr.b $3d(a2)           ; no skew
        move.b #$80,$3c(a2)     ; shared-bus mode, interrupts remain enabled
.busy:
        bset #7,$3c(a2)         ; same restart/wait as SuperHex blit_go
        nop
        bne.s .busy
        move.l (sp)+,a2
        rts
Wedges_CopyEnd:
; Startup-only packed-plane horizontal span. a0 row, d0 left, d1 right.
; Edge masks and whole-word stores; never used by the animation copy path.
        xdef Wedges_Span
Wedges_Span:
        movem.l d2-d4,-(sp)
        tst.w d0
        bge.s .leftOK
        moveq #0,d0
.leftOK:
        cmp.w #319,d1
        ble.s .rightOK
        move.w #319,d1
.rightOK:
        cmp.w d0,d1
        blt.s .done
        move.w d0,d2
        and.w #15,d2
        moveq #-1,d3
        lsr.w d2,d3
        move.w d1,d2
        and.w #15,d2
        moveq #15,d4
        sub.w d2,d4
        moveq #-1,d2
        lsl.w d4,d2
        lsr.w #4,d0
        lsr.w #4,d1
        sub.w d0,d1
        add.w d0,d0
        adda.w d0,a0
        tst.w d1
        bne.s .many
        and.w d2,d3
        or.w d3,(a0)
        bra.s .done
.many:
        or.w d3,(a0)+
        subq.w #2,d1
        bmi.s .right
        moveq #-1,d4
.middle:
        move.w d4,(a0)+
        dbra d1,.middle
.right:
        or.w d2,(a0)
.done:
        movem.l (sp)+,d2-d4
        rts
        section data
        even
        xdef Wedges_Sine
Wedges_Sine:
        include 'assets/SINE.S'
