        section text
        xdef PsgExtra_Init,PsgExtra_Update,PsgExtra_UpdateEnd
        xdef PsgPiano_Init,PsgPiano_Draw,PsgPiano_DrawEnd
        xdef PsgScope_Prepare,PsgScope_PrepareEnd,PsgScope_Draw,PsgScope_DrawEnd
        xdef PsgCircles_Draw,PsgCircles_DrawEnd
        xref gPsgNotes,gPsgNoteSerial,gPsgPeriods,gPsgToneLevels
PsgExtra_Init:
        lea gPsgNotes,a0
        moveq #-1,d0
        move.w d0,(a0)+
        move.w d0,(a0)+
        move.w d0,(a0)+
        rts
; Global animation state is updated once/frame even while hidden.
PsgExtra_Update:
        movem.l d2-d7/a2-a5,-(sp)
        lea gPianoKeys,a0
        moveq #19,d0
.clear:
        clr.l (a0)+
        dbf d0,.clear
        lea gRingAges,a0
        moveq #11,d0
.age:
        tst.w (a0)
        beq.s .age_next
        addq.w #1,(a0)
        cmpi.w #25,(a0)
        bne.s .age_next
        clr.w (a0)
.age_next:
        addq.l #2,a0
        dbf d0,.age
        lea gPsgNotes,a0
        lea gPsgNoteSerial,a1
        lea Extra_LastSerial,a2
        lea Extra_NextRing,a3
        lea gPianoKeys,a4
        lea gRingAges,a5
        moveq #0,d6
.channel:
        move.w (a0)+,d0
        cmpi.w #80,d0
        bhs.s .no_key
        bset d6,(a4,d0.w)
.no_key:
        move.w (a1)+,d1
        cmp.w (a2),d1
        beq.s .no_ring
        move.w d1,(a2)
        cmpi.w #80,d0
        bhs.s .no_ring
        move.w (a3),d2
        move.w d6,d3
        lsl.w #2,d3
        add.w d2,d3
        add.w d3,d3
        move.w #1,(a5,d3.w)
        addq.w #1,d2
        andi.w #3,d2
        move.w d2,(a3)
.no_ring:
        addq.l #2,a2
        addq.l #2,a3
        addq.w #1,d6
        cmpi.w #3,d6
        bne.s .channel
        movem.l (sp)+,d2-d7/a2-a5
        rts
PsgExtra_UpdateEnd:
; a0 = Back canvas VRAM. Copy only the static keyboard rectangle.
PsgPiano_Init:
        lea 72*160(a0),a0
        lea Piano_Image,a1
        move.w #2559,d0
.copy:
        move.l (a1)+,(a0)+
        dbf d0,.copy
        rts
; a0=screen, a1=80 channel masks, 4(sp)=80 previous masks for this page.
PsgPiano_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l 48(sp),a4
        lea 72*160(a0),a2
        lea Piano_KeyOffsets,a6
        moveq #79,d7
.key:
        moveq #0,d0
        move.b (a1)+,d0
        cmp.b (a4),d0
        beq.s .skip
        move.b d0,(a4)+
        lea Piano_Keys,a3
        adda.l (a6),a3
        move.w (a3)+,d6
        subq.w #1,d6
.record:
        moveq #0,d1
        move.w (a3)+,d1
        move.w (a3)+,d2
        move.w d2,d3
        not.w d3
        move.l a2,a0
        adda.w d1,a0
        tst.w d0
        beq.s .restore
        move.w d0,d4
        lsl.w #3,d4
        lea Piano_Colors,a5
        adda.w d4,a5
        bra.s .words
.restore:
        lea Piano_Image,a5
        adda.w d1,a5
.words:
        rept 4
        move.w (a0),d4
        and.w d3,d4
        move.w (a5)+,d5
        and.w d2,d5
        or.w d5,d4
        move.w d4,(a0)+
        endr
        dbf d6,.record
        bra.s .next
.skip:
        addq.l #1,a4
.next:
        addq.l #4,a6
        dbf d7,.key
        movem.l (sp)+,d2-d7/a2-a6
        rts
PsgPiano_DrawEnd:
; Each channel is just {phase step, graphical amplitude}; no sample buffers.
PsgScope_Prepare:
        movem.l d2/a2-a3,-(sp)
        lea gScopeParams,a0
        lea gPsgPeriods,a1
        lea gPsgToneLevels,a2
        lea Scope_Steps,a3
        moveq #2,d2
.channel:
        move.w (a1)+,d0
        move.w (a2)+,d1
        add.w d1,d1
        add.w -2(a2),d1
        lsr.w #2,d1
        beq.s .flat
        add.w d0,d0
        move.w (a3,d0.w),(a0)+
        bra.s .amplitude
.flat:
        clr.w (a0)+
.amplitude:
        move.w d1,(a0)+
        dbf d2,.channel
        movem.l (sp)+,d2/a2-a3
        rts
PsgScope_PrepareEnd:
; a0=screen, a1=3 {U16 phase step, U16 amplitude}, 4(sp)=previous params.
; Each page owns its six words of history, initialized to $ffff.
PsgScope_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l 48(sp),a4
        lea 52*160+16(a0),a3
        lea Scope_Rows,a6
        move.w #2,-(sp)
.channel:
        move.l (a1)+,d2
        move.l (a4),d3
        cmp.l d2,d3
        beq.s .unchanged
        move.l d2,(a4)+
        move.l d2,-(sp)
        cmpi.w #-1,d3
        beq.s .new
        move.w d3,d1
        swap d3
        move.w d3,d0
        bsr .trace
.new:
        move.l (sp)+,d0
        move.w d0,d1
        swap d0
        bsr .trace
        bra.s .next_channel
.unchanged:
        addq.l #4,a4
.next_channel:
        adda.w #6402,a3
        subq.w #1,(sp)
        bpl.s .channel
        addq.l #2,sp
        movem.l (sp)+,d2-d7/a2-a6
        rts
; d0=16-bit phase step, d1=amplitude 0..12. Same 256 sampled positions as
; before, but divide directly to the next half-cycle boundary instead of
; generating/scanning every sample. Reverse phase handles steps above Nyquist.
.trace:
        moveq #12,d6
        sub.w d1,d6
        moveq #12,d7
        add.w d1,d7
        swap d7
        move.w d6,d7
        moveq #0,d5
        tst.w d1
        bne.s .wave
        move.w #256,d4
        bra .horizontal
 .wave:
; One division per trace: half-cycle = quotient*step + remainder. Carry the
; remainder between runs instead of dividing/multiplying at every edge.
        moveq #0,d2
        cmpi.w #32768,d0
        bls.s .forward
        neg.w d0
        moveq #1,d2
.forward:
        move.w d0,-(sp)          ; absolute step
        move.l #32768,d1
        divu.w d0,d1
        move.w d1,-(sp)          ; integer pixels per half-cycle
        swap d1
        move.w d1,-(sp)          ; fractional remainder
        tst.w d2
        bne.s .reverse_first
        subq.w #1,d0
        move.w d0,-(sp)          ; ceil boundaries for forward phase
        bra.s .run
.reverse_first:
        clr.w -(sp)             ; floor boundaries after first reverse sample
        moveq #1,d0
        bra.s .length
.run:
        move.w 4(sp),d0
        move.w (sp),d1
        add.w 2(sp),d1
        cmp.w 6(sp),d1
        blo.s .no_carry
        sub.w 6(sp),d1
        addq.w #1,d0
.no_carry:
        move.w d1,(sp)
.length:
        move.w #256,d1
        sub.w d5,d1
        cmp.w d1,d0
        bls.s .bounded
        move.w d1,d0
.bounded:
        move.w d5,d4
        add.w d0,d4
        bsr .horizontal
        cmpi.w #256,d4
        beq.s .done
        swap d7
        move.w d7,d0
        bsr .vertical
        move.w d7,d6
        move.w d4,d5
        bra .run
.done:
        addq.l #8,sp
        rts
; Horizontal run [d5,d4), at row d6. Preserve d4-d7/a1/a3-a6.
.horizontal:
        move.w d5,d0
        andi.w #15,d0
        moveq #-1,d2
        lsr.w d0,d2
        move.w d4,d0
        andi.w #15,d0
        moveq #-1,d3
        tst.w d0
        beq.s .end_mask
        moveq #16,d1
        sub.w d0,d1
        lsl.w d1,d3
.end_mask:
        move.w d6,d0
        add.w d0,d0
        move.l a3,a0
        adda.w (a6,d0.w),a0
        move.l a0,a2
        move.w d5,d0
        lsr.w #4,d0
        lsl.w #3,d0
        adda.w d0,a0
        move.w d4,d0
        subq.w #1,d0
        lsr.w #4,d0
        lsl.w #3,d0
        adda.w d0,a2
        cmpa.l a2,a0
        bne.s .first_word
        and.w d3,d2
        eor.w d2,(a0)
        rts
.first_word:
        eor.w d2,(a0)
        addq.l #8,a0
.middle:
        cmpa.l a2,a0
        beq.s .last_word
        not.w (a0)
        addq.l #8,a0
        bra.s .middle
.last_word:
        eor.w d3,(a0)
        rts
; Edge at x=d4, from previous height d6 up to (excluding) new height d0.
; The new horizontal run includes that endpoint, so XOR never cancels it.
.vertical:
        move.w d6,d1
        cmp.w d0,d1
        bls.s .down
        exg d0,d1
        addq.w #1,d1
        addq.w #1,d0
 .down:
        sub.w d1,d0
        subq.w #1,d0           ; length minus one
        move.w d0,d3
        add.w d1,d3            ; last row
        add.w d3,d3
        move.l a3,a0
        adda.w (a6,d3.w),a0
        move.w d4,d1
        lsr.w #4,d1
        lsl.w #3,d1
        adda.w d1,a0
        move.w d4,d1
        andi.w #15,d1
        move.w #$8000,d2
        lsr.w d1,d2
        moveq #23,d1
        sub.w d0,d1
        lsl.w #2,d1
        jmp .edge(pc,d1.w)
.edge:
N       set -23
        rept 24
        eor.w d2,N*160(a0)
N       set N+1
        endr
        rts
PsgScope_DrawEnd:

; a0=screen, a1=12 U16 ages, 4(sp)=12 previous ages, initially zero.
; Fused XOR deltas handle ordinary two-frame page revisits. Arbitrary jumps
; (retrigger, hide/show, expiry) erase/draw with the single-frame kernels.
PsgCircles_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l 48(sp),a4
        move.l a0,a2
        lea Rings_Centers,a5
        lea Rings_Kernels,a6
        move.w #$8000,d3
        moveq #8,d4
        moveq #1,d5
        moveq #2,d6
        moveq #11,d7
.ring:
        move.l a2,a3
        adda.w (a5)+,a3
        move.w (a4),d0
        move.w (a1)+,d1
        move.w d1,(a4)+
        cmp.w d0,d1
        beq.s .next
        move.w d1,d2
        sub.w d0,d2
        cmpi.w #2,d2
        bne.s .separate
        move.w d1,d0
        lsl.w #2,d0
        move.l a6,a0
        adda.l Rings_Delta2Offsets-Rings_Kernels(a6,d0.w),a0
        jsr (a0)
        bra.s .next
.separate:
        lsl.w #2,d0
        move.l a6,a0
        adda.l Rings_SingleOffsets-Rings_Kernels(a6,d0.w),a0
        jsr (a0)
        lsl.w #2,d1
        move.l a6,a0
        adda.l Rings_SingleOffsets-Rings_Kernels(a6,d1.w),a0
        jsr (a0)
.next:
        dbf d7,.ring
        movem.l (sp)+,d2-d7/a2-a6
        rts
        include 'assets/RINGS.S'
PsgCircles_DrawEnd:
Scope_Rows:
N       set 0
        rept 25
        dc.w N*160
N       set N+1
        endr
Rings_Centers:
        rept 4
        dc.w 100*160+40
        endr
        rept 4
        dc.w 100*160+80+2
        endr
        rept 4
        dc.w 100*160+120+4
        endr
        section data
        even
Piano_Image: incbin 'assets/PIANO.BIN'
Piano_KeyOffsets: incbin 'assets/KEYOFF.BIN'
Piano_Keys: incbin 'assets/KEYS.BIN'
Piano_Colors:
N       set 0
        rept 8
        dc.w -(N&1),-((N>>1)&1),-((N>>2)&1),-1
N       set N+1
        endr
Scope_Steps: incbin 'assets/SCOPESTEP.BIN'
        section bss
        even
        xdef gPianoKeys,gScopeParams,gRingAges
 gPianoKeys: ds.b 80
 gScopeParams: ds.w 6
 gRingAges: ds.w 12
Extra_LastSerial: ds.w 3
Extra_NextRing: ds.w 3
