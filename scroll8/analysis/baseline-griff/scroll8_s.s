; MCoder: SCROL2.S, The Lonely Coder.
; Griff: bufsc8.s, Martin Griffiths / Electronic Images, Sept 1990.
; GodLib adaptations: shared ASCII/font, explicit screen pointer, ABI saves,
; separate pause image copy and queue warmup. Original phase/copy algorithms kept.
        section text
        xdef MCoder_Update,MCoder_UpdateEnd,MCoder_Copy,MCoder_CopyEnd
        xdef Griff_Update,Griff_UpdateEnd,Griff_Copy,Griff_CopyEnd
        xdef Tiny_CopyPaused
        xref gFont8x8,gTinyText,gTinyScreen,gTinyPreviousScreen
        xref gTinyMCText,gTinyMCPhase,gTinyMCPos,gTinyMCDisplay
        xref gTinyGText,gTinyGPhase,gTinyGPos,gTinyGPhaseBase,gTinyGDisplay
MCoder_Update:
        movem.l d0-d7/a0-a6,-(sp)
        move.w gTinyMCPhase,d7
        lea gTinyMCBuffer,a0
        move.w d7,d0
        mulu #320,d0
        adda.w d0,a0
        adda.w gTinyMCPos,a0
        move.l a0,gTinyMCDisplay
        bsr MCoder_Copy
        move.l gTinyMCText,a6
        moveq #0,d0
        move.b (a6)+,d0
        sub.w #32,d0
        asl.w #3,d0
        lea gFont8x8,a4
        adda.w d0,a4
        moveq #0,d0
        move.b (a6),d0
        bne.s .right
        lea gTinyText,a6
        move.b (a6),d0
.right:
        sub.w #32,d0
        asl.w #3,d0
        lea gFont8x8,a5
        adda.w d0,a5
        move.w gTinyMCPhase,d7
        lea gTinyMCBuffer,a0
        move.w d7,d0
        mulu #320,d0
        adda.w d0,a0
        adda.w gTinyMCPos,a0
X       set 0
Y       set 0
        rept 8
        movep.w X(a5),d0
        move.b (a4)+,d0
        rol.w d7,d0
        move.b d0,Y(a0)
        move.b d0,Y+40(a0)
X       set X+1
Y       set Y+80
        endr
        addq.w #2,gTinyMCPhase
        and.w #7,gTinyMCPhase
        bne.s .done
        move.l a6,gTinyMCText
        addq.w #1,gTinyMCPos
        cmp.w #40,gTinyMCPos
        blo.s .done
        clr.w gTinyMCPos
.done:
        movem.l (sp)+,d0-d7/a0-a6
        rts
MCoder_UpdateEnd:
MCoder_Copy:
        move.l gTinyMCDisplay,a0
        move.l gTinyScreen,a1
        lea 88*160(a1),a1
        moveq #7,d0
.row:
        rept 20
        move.b (a0)+,(a1)+
        move.b (a0)+,(a1)+
        addq.l #6,a1
        endr
        lea 40(a0),a0
        dbf d0,.row
        rts
MCoder_CopyEnd:
Griff_Update:
        movem.l d0-d7/a0-a6,-(sp)
        move.l gTinyGText,a0
        move.l gTinyGPhaseBase,a3
        move.w gTinyGPhase,d2
        lea 2048(a3),a3
        addq.w #2,d2
        cmp.w #16,d2
        bne.s .position
        addq.w #2,gTinyGPos
        cmp.w #64,gTinyGPos
        bne.s .nowrap
        clr.w gTinyGPos
.nowrap:
        lea gTinyGBuffer,a3
        moveq #0,d2
        addq.l #2,a0
.position:
        tst.b 1(a0)
        bne.s .text
        lea gTinyText,a0
.text:
        move.w d2,gTinyGPhase
        move.l a3,gTinyGPhaseBase
        move.l a0,gTinyGText
        moveq #0,d0
        moveq #0,d1
        move.b (a0)+,d0
        move.b (a0),d1
        sub.b #32,d0
        sub.b #32,d1
        lsl.w #3,d0
        lsl.w #3,d1
        lea gFont8x8,a0
        lea (a0),a2
        adda.w d0,a0
        adda.w d1,a2
        adda.w gTinyGPos,a3
        move.l a3,gTinyGDisplay
        moveq #7,d0
.addin:
        moveq #0,d3
        move.b (a0)+,d3
        lsl.w #8,d3
        move.b (a2)+,d3
        rol.l d2,d3
        move.w d3,-2(a3)
        move.w d3,62(a3)
        swap d3
        or.w d3,-4(a3)
        or.w d3,60(a3)
        swap d3
        ; Retain upstream's second (odd) phase, even though speed 2 displays
        ; only even phases. Removing it would be an additional optimization.
        rol.l #1,d3
        move.w d3,1024-2(a3)
        move.w d3,1024+62(a3)
        swap d3
        or.w d3,1024-4(a3)
        or.w d3,1024+60(a3)
        lea 128(a3),a3
        dbf d0,.addin
        bsr Griff_Copy
        movem.l (sp)+,d0-d7/a0-a6
        rts
Griff_UpdateEnd:
Griff_Copy:
        move.l gTinyScreen,a0
        lea 120*160(a0),a0
        move.l gTinyGDisplay,a2
        moveq #7,d0
.row:
X       set 0
        rept 20
        move.w (a2)+,X(a0)
X       set X+8
        endr
        lea 88(a2),a2
        lea 160(a0),a0
        dbf d0,.row
        rts
Griff_CopyEnd:
Tiny_CopyPaused:
        movem.l d0/a0-a1,-(sp)
        move.l gTinyPreviousScreen,a0
        move.l gTinyScreen,a1
        moveq #7,d0
.pause0:
X       set 0
        rept 20
        move.w X+88*160(a0),X+88*160(a1)
X       set X+8
        endr
        lea 160(a0),a0
        lea 160(a1),a1
        dbf d0,.pause0
        moveq #7,d0
.pause1:
X       set 0
        rept 20
        move.w X+112*160(a0),X+112*160(a1)
X       set X+8
        endr
        lea 160(a0),a0
        lea 160(a1),a1
        dbf d0,.pause1
        movem.l (sp)+,d0/a0-a1
        rts
; Debug only: wait for the counter to reach visible row 32. ST screen pages
; are 256-byte aligned, and 32*160=5120 is exactly twenty 256-byte blocks.
; Equality avoids accepting the previous frame's end counter during VBL.
; The wait is outside the coloured/measured work. A0 = physical page (fastcall).
        xdef Tiny_RasterSync,Tiny_RasterSyncEnd
Tiny_RasterSync:
        movem.l d0-d1/a1,-(sp)
        move.l a0,d0
        lsr.l #8,d0
        add.w #20,d0
        lea $ffff8205.w,a1
.wait:
        movep.w 0(a1),d1
        cmp.w d0,d1
        bne.s .wait
        movem.l (sp)+,d0-d1/a1
        rts
Tiny_RasterSyncEnd:
        section .bss,bss
        even
        xdef gTinyMCBuffer,gTinyGStorage,gTinyGBuffer
; Extra leading/trailing words are required by Griff's -4/-2 stores.
gTinyMCBuffer: ds.b 2560
gTinyGStorage: ds.w 2
gTinyGBuffer: ds.b 16384
        ds.w 2
