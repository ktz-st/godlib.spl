; DCK TEXT $354A: volume-value buckets, not frequency bands.
; GodLib adaptation: byte counters, coherent RAM snapshot and per-page deltas.
        section text
        xdef PsgHistogram_Reset,PsgHistogram_ResetEnd
        xdef PsgHistogram_Update,PsgHistogram_UpdateEnd
        xdef PsgHistogram_Draw,PsgHistogram_DrawEnd
        xref gPsgRegisters
PsgHistogram_Reset:
        lea gPsgHistogram,a0
        clr.l (a0)+
        clr.l (a0)+
        clr.l (a0)+
        clr.l (a0)
        rts
PsgHistogram_ResetEnd:
PsgHistogram_Update:
        movem.l d2-d3/a2,-(sp)
        lea gPsgHistogram,a0
        moveq #15,d0
.decay:
        tst.b (a0)+
        beq.s .next
        subq.b #1,-1(a0)
.next:
        dbf d0,.decay
        ; The replay chaser supplies gPsgRegisters. Never write YM data here.
        ; Lock only the three RAM reads, then release interrupts before drawing.
        move.w sr,-(sp)
        move.w #$2700,sr
        moveq #0,d1
        moveq #0,d2
        moveq #0,d3
        move.b gPsgRegisters+8,d1
        move.b gPsgRegisters+9,d2
        move.b gPsgRegisters+10,d3
        move.w (sp)+,sr
        andi.w #15,d1
        andi.w #15,d2
        andi.w #15,d3
        lea gPsgHistogram,a0
        move.b #32,0(a0,d1.w)
        move.b #32,0(a0,d2.w)
        move.b #32,0(a0,d3.w)
        movem.l (sp)+,d2-d3/a2
        rts
PsgHistogram_UpdateEnd:
; GCC fastcall: a0=screen, a1=16 byte counters; third argument at 4(sp).
PsgHistogram_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l 48(sp),a4
        lea 143*160+16(a0),a2    ; 16 bars x 16px, centred at X=32..287
        lea PsgHistogram_Rows(pc),a6
        moveq #15,d7
.bar:
        moveq #0,d0
        moveq #0,d1
        move.b (a1)+,d0
        move.b (a4),d1
        move.b d0,(a4)+
        cmp.w d1,d0
        beq.s .next
        move.l a2,a0
        bhi.s .grow
        sub.w d0,d1
        add.w d0,d0
        move.w 0(a6,d0.w),d0
        suba.w d0,a0
        subq.w #1,d1
.erase:
        clr.w (a0)
        lea -160(a0),a0
        dbf d1,.erase
        bra.s .next
.grow:
        sub.w d1,d0
        add.w d1,d1
        move.w 0(a6,d1.w),d1
        suba.w d1,a0
        subq.w #1,d0
.draw:
        move.w #$fffe,(a0)       ; 15 pixels and a one-pixel gap
        lea -160(a0),a0
        dbf d0,.draw
.next:
        addq.l #8,a2
        dbf d7,.bar
        movem.l (sp)+,d2-d7/a2-a6
        rts
PsgHistogram_DrawEnd:
PsgHistogram_Rows:
N       set 0
        rept 33
        dc.w N*160
N       set N+1
        endr
        section bss
        even
        xdef gPsgHistogram
 gPsgHistogram: ds.b 16
