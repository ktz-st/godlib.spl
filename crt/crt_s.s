; STe CRT: three picture planes + independent dark-row mask. Stride 160.
        section text
        xdef Crt_Render,Crt_RenderEnd,Crt_ImageUpdate,Crt_ImageUpdateEnd
        xdef Crt_MaskUpdate,Crt_MaskUpdateEnd
        xref gCrtScreen,gCrtHistory,gCrtX,gCrtY,gCrtBand,gCrtScan,gCrtSource
Crt_Render:
        movem.l d2-d7/a2-a6,-(sp)
        bsr Crt_ImageUpdate
        bsr Crt_MaskUpdate
        movem.l (sp)+,d2-d7/a2-a6
        rts
Crt_RenderEnd:
; Only re-blit bands whose shift changed on this display page. Adjacent bands
; with the same new X shift coalesce into one run, including unchanged bands.
Crt_ImageUpdate:
        move.l gCrtHistory,a6
        lea gCrtX,a5
        move.l gCrtScreen,a4
        lea 16*160(a4),a4
        move.w 22(a6),d6
        move.w gCrtY,d5
        move.w d5,22(a6)
        moveq #16,d2
        moveq #11,d7
.band:
        move.w (a5)+,d4
        move.w (a6),d0
        move.w d4,(a6)+
        moveq #16,d3
        cmp.w d5,d6
        bne.s .changed
        cmp.w d0,d4
        beq.s .advance
.changed:
        cmpi.w #1,d7
        beq.s .draw
        cmp.w (a5),d4
        bne.s .draw
        addq.l #2,a5
        move.w d4,(a6)+
        addi.w #16,d3
        subq.w #1,d7
        bra.s .changed
.draw:
        bsr .blit
.advance:
        add.w d3,d2
        move.w d3,d0
        mulu.w #160,d0
        adda.l d0,a4
        subq.w #1,d7
        bne.s .band
        rts
; a4 = destination p0, d2 = first row, d3 = height, d4 = X, d5 = Y.
; Source has 22 words/row, 204 rows/plane: guard words and two guard rows.
; The three image planes are separate in the source, interleaved in VRAM.
.blit:
        move.w d2,d0
        sub.w d5,d0
        addq.w #2,d0
        mulu.w #44,d0
        move.l gCrtSource,a2
        adda.l d0,a2
        moveq #0,d1
        tst.w d4
        bgt.s .right
        addq.l #2,a2
        beq.s .aligned
        moveq #16,d1
        add.w d4,d1
        bra.s .skew
.right:
        move.w d4,d1
.skew:
        ori.w #$80,d1
.aligned:
        lea $ffff8a00.w,a1
        move.w #2,$20(a1)
        moveq #6,d0
        tst.w d4
        beq.s .stride
        moveq #4,d0
.stride:
        move.w d0,$22(a1)
        move.w #-1,$28(a1)
        move.w #-1,$2a(a1)
        move.w #-1,$2c(a1)
        move.w #8,$2e(a1)
        move.w #8,$30(a1)
        move.b #2,$3a(a1)
        move.b #3,$3b(a1)
        move.b d1,$3d(a1)
        move.l a4,a3
        moveq #2,d0
.plane:
        move.l a2,$24(a1)
        move.l a3,$32(a1)
        move.w #20,$36(a1)
        move.w d3,$38(a1)
; Shared mode; do not mask interrupts or hold the bus for a whole screen.
        move.b #$80,$3c(a1)
.wait:
        bset #7,$3c(a1)
        nop
        bne.s .wait
        adda.w #8976,a2
        addq.l #2,a3
        dbf d0,.plane
        rts
Crt_ImageUpdateEnd:
; Mask history is just old band + scanline enable. Update the symmetric
; difference of the old/new bright intervals; no full image-row scan.
Crt_MaskUpdate:
        move.l gCrtScreen,a2
        lea 16*160+6(a2),a2
        move.l gCrtHistory,a1
        lea 24(a1),a1
        move.w (a1),d0
        move.w gCrtBand,(a1)
        bsr .clip
        move.w d0,d2
        move.w d1,d3
        move.w gCrtBand,d0
        bsr .clip
        move.w d0,d4
        move.w d1,d5
        move.w 2(a1),d7
        move.w gCrtScan,d0
        move.w d0,2(a1)
        tst.w d0
        beq.s .off
        tst.w d7
        beq.s .on
        moveq #-1,d6            ; old bright minus new bright -> dark
        bsr .difference
        exg d2,d4
        exg d3,d5
        moveq #0,d6             ; new bright minus old bright -> bright
        bra .difference
.off:
        tst.w d7
        beq.s .done
        moveq #0,d6
        moveq #0,d0
        move.w #176,d1
        bra .span
.on:
        moveq #-1,d6
        moveq #0,d0
        move.w #176,d1
        bsr .span
        moveq #0,d6
        move.w d4,d0
        move.w d5,d1
        bra .span
; [d2,d3) minus [d4,d5), fill with d6. Preserve interval registers.
.difference:
        cmp.w d3,d2
        bge.s .done
        cmp.w d4,d2
        bge.s .tail
        move.w d2,d0
        move.w d3,d1
        cmp.w d4,d1
        ble.s .head
        move.w d4,d1
.head:
        bsr .span
.tail:
        cmp.w d5,d3
        ble.s .done
        move.w d2,d0
        cmp.w d5,d0
        bge.s .tail_ready
        move.w d5,d0
.tail_ready:
        move.w d3,d1
        bra .span
.done:
        rts
; d0=band start -> d0/d1 clipped half-open interval within [0,176].
.clip:
        move.w d0,d1
        addi.w #22,d1
        tst.w d0
        bpl.s .start_positive
        moveq #0,d0
.start_positive:
        cmpi.w #176,d0
        ble.s .clip_end
        move.w #176,d0
.clip_end:
        tst.w d1
        bpl.s .end_positive
        moveq #0,d1
.end_positive:
        cmpi.w #176,d1
        ble.s .done
        move.w #176,d1
        rts
; Fill only odd picture rows in [d0,d1). a2 = row 0 plane 3, mask in d6.
.span:
        ori.w #1,d0
        subq.w #1,d1
        sub.w d0,d1
        bmi.s .done
        lsr.w #1,d1
        mulu.w #160,d0
        move.l a2,a0
        adda.l d0,a0
.row:
N       set 0
        rept 20
        move.w d6,N*8(a0)
N       set N+1
        endr
        lea 320(a0),a0
        dbf d1,.row
        rts
Crt_MaskUpdateEnd:
        section data
        even
        xdef Crt_Image,Crt_Palette,Crt_Source,Crt_Image2,Crt_Palette2,Crt_Source2
Crt_Palette: incbin 'assets/PALETTE.BIN'
Crt_Image: incbin 'assets/IMAGE.BIN'
Crt_Source: incbin 'assets/SOURCE.BIN'

Crt_Palette2: incbin 'assets/PALETTE2.BIN'
Crt_Image2: incbin 'assets/IMAGE2.BIN'
Crt_Source2: incbin 'assets/SOURCE2.BIN'
