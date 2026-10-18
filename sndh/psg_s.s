        section text
        xdef PsgVis_Replay,PsgVis_ReplayEnd,PsgVis_Snapshot,PsgVis_SnapshotEnd
        xdef PsgVis_Update,PsgVis_UpdateEnd
        xref gSndVisPlay,gSndVisRaster
; Snd_Player already preserves all registers around replay and chaser.
PsgVis_Replay:
        tst.w gSndVisRaster
        beq.s .plain
        move.w $ffff8240.w,-(sp)
        move.w #$700,$ffff8240.w
        move.l gSndVisPlay,a0
        jsr (a0)
        move.w (sp)+,$ffff8240.w
        rts
.plain:
        move.l gSndVisPlay,a0
        jmp (a0)
PsgVis_ReplayEnd:
; Called immediately after replay, never from raster drawing. No YM data writes.
; Example supports conventional TC replay; no digi/SID ISR latch assumptions.
PsgVis_Snapshot:
        move.w sr,-(sp)
        move.w #$2700,sr
        lea $ffff8800.w,a0
        lea gPsgRegisters,a1
        moveq #0,d0
.loop:
        move.b d0,(a0)
        move.b (a0),(a1)+
        addq.w #1,d0
        cmpi.w #11,d0
        bne.s .loop
        move.w (sp)+,sr
        rts
PsgVis_SnapshotEnd:
; Main loop only: decay once/frame, then trigger current notes. R7 tone-off
; channels do not trigger note bands. Noise can still light the volume meters.
PsgVis_Update:
        movem.l d2-d7/a2-a5,-(sp)
        lea gPsgBands,a0
        moveq #79,d0
.decay:
        tst.b (a0)+
        beq.s .next
        subq.b #1,-1(a0)
.next:
        dbf d0,.decay
; Coherent RAM snapshot, keep the hardware lock out of the drawing phase.
        suba.w #12,sp
        move.w sr,-(sp)
        move.w #$2700,sr
        lea gPsgRegisters,a0
        lea 2(sp),a1
        moveq #10,d0
.copy:
        move.b (a0)+,(a1)+
        dbf d0,.copy
        move.w (sp)+,sr
        move.l sp,a0
        lea gPsgLevels,a1
        lea gPsgEnvelope,a2
        lea PsgVis_Notes,a3
        lea gPsgBands,a4
        moveq #0,d6
        moveq #0,d7
.channel:
        moveq #0,d4
        move.b 1(a0,d7.w),d4
        andi.w #15,d4
        lsl.w #8,d4
        move.b (a0,d7.w),d4
        lea gPsgPeriods,a5
        move.w d4,(a5,d7.w)
        lea gPsgToneLevels,a5
        clr.w (a5,d7.w)
        moveq #-1,d5
        moveq #0,d0
        move.b 8(a0,d6.w),d0
        move.w d0,d1
        andi.w #16,d1
        move.w d1,(a2)+
        andi.w #15,d0
        beq.s .envelope
        addq.w #1,d0        ; states 1..16 hold source artwork 0..15
.envelope:
        tst.w d1
        beq.s .fixed
        moveq #16,d0
.fixed:
        move.b 7(a0),d2
        btst d6,d2
        beq.s .volume
        move.w d6,d3
        addq.w #3,d3
        btst d3,d2
        beq.s .volume
        moveq #0,d0          ; both tone and noise disabled
.volume:
        move.w d0,(a1)+
        tst.w d0
        beq.s .advance
        btst d6,d2
        bne.s .advance
        move.w d0,(a5,d7.w)
        move.w d4,d1
        moveq #0,d2
        move.b (a3,d1.w),d2
        move.b #12,(a4,d2.w)
        move.w d2,d5
.advance:
        lea gPsgNotes,a5
        cmp.w (a5,d7.w),d5
        beq.s .same_note
        move.w d5,(a5,d7.w)
        lea gPsgNoteSerial,a5
        addq.w #1,(a5,d7.w)
.same_note:
        addq.w #2,d7
        addq.w #1,d6
        cmpi.w #3,d6
        bne.w .channel
        adda.w #12,sp
        movem.l (sp)+,d2-d7/a2-a5
        rts
PsgVis_UpdateEnd:
        section data
        even
PsgVis_Notes: incbin 'assets/NOTES.BIN'
        section bss
        even
        xdef gPsgRegisters,gPsgLevels,gPsgEnvelope,gPsgBands
 gPsgRegisters: ds.b 12
 gPsgLevels: ds.w 3
 gPsgEnvelope: ds.w 3
 gPsgBands: ds.b 80

        xdef gPsgPeriods,gPsgToneLevels,gPsgNotes,gPsgNoteSerial
 gPsgPeriods: ds.w 3
 gPsgToneLevels: ds.w 3
 gPsgNotes: ds.w 3
 gPsgNoteSerial: ds.w 3
