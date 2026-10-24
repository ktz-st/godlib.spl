; DCK PSG horizontal / segmented bar styles, GodLib delta drawing.
; Source layouts: TEXT $321C, $35F6, $3664, $36E0. Existing PSG levels 0..16.
        section text
        xdef PsgDck_Reset,PsgDck_ResetEnd,PsgDck_Update,PsgDck_UpdateEnd
        xdef PsgDck_Draw0,PsgDck_Draw1,PsgDck_Draw2,PsgDck_Draw3,PsgDck_DrawEnd
        xref gPsgLevels
PsgDck_Reset:
        clr.l gPsgDckLevels
        clr.w gPsgDckLevels+4
        rts
PsgDck_ResetEnd:
PsgDck_Update:
        lea gPsgLevels,a0
        lea gPsgDckLevels,a1
        moveq #2,d0
.loop:
        tst.w (a1)
        beq.s .sample
        subq.w #1,(a1)
.sample:
        move.w (a0)+,d1
        cmp.w (a1),d1
        bls.s .next
        move.w d1,(a1)
.next:
        addq.l #2,a1
        dbf d0,.loop
        rts
PsgDck_UpdateEnd:
; a0=screen, a1=three U16 levels, 4(sp)=three previous U16 levels for this page.
PsgDck_Draw0:
        moveq #0,d0
        bra.s PsgDck_Draw
PsgDck_Draw1:
        moveq #1,d0
        bra.s PsgDck_Draw
PsgDck_Draw2:
        moveq #2,d0
        bra.s PsgDck_Draw
PsgDck_Draw3:
        moveq #3,d0
PsgDck_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l 48(sp),a4
        tst.w d0
        beq.w .horizontal
        subq.w #1,d0
        lsl.w #3,d0
        lea .config(pc),a6
        adda.w d0,a6
        lea 168*160(a0),a2
        adda.w (a6)+,a2
        move.w (a6)+,d5         ; width type
        move.w (a6)+,d6         ; level scale shift
        move.w (a6)+,d4         ; next-channel byte stride
        lea PsgDck_Rows(pc),a6
        moveq #2,d7
.channel:
        move.w (a1)+,d0
        move.w (a4),d1
        move.w d0,(a4)+
        cmp.w d1,d0
        beq.s .vnext
        lsl.w d6,d0
        lsl.w d6,d1
        move.l a2,a0
        cmp.w d1,d0
        bhi.s .grow
        move.w d1,d2
        sub.w d0,d2
        add.w d0,d0
        suba.w 0(a6,d0.w),a0
        moveq #0,d3
        bra.s .span
.grow:
        move.w d0,d2
        sub.w d1,d2
        add.w d1,d1
        suba.w 0(a6,d1.w),a0
        moveq #-1,d3
.span:
        subq.w #1,d2
        tst.w d5
        beq.s .width16
        cmpi.w #1,d5
        beq.s .width32
.width80:
        move.b d3,(a0)
        move.w d3,7(a0)
        move.w d3,15(a0)
        move.w d3,23(a0)
        move.w d3,31(a0)
        move.b d3,39(a0)
        lea -320(a0),a0
        dbf d2,.width80
        bra.s .vnext
.width32:
        move.w d3,(a0)
        move.w d3,8(a0)
        lea -320(a0),a0
        dbf d2,.width32
        bra.s .vnext
.width16:
        move.b d3,(a0)
        move.b d3,7(a0)
        lea -320(a0),a0
        dbf d2,.width16
.vnext:
        adda.w d4,a2
        dbf d7,.channel
        bra.w .done
; first byte, width kind, scale shift, per-channel stride (includes plane +2)
.config: dc.w 57,0,1,18, 40,1,2,34, 9,2,2,50
.horizontal:
        lea 64*160+16(a0),a2
        moveq #2,d7
.hchannel:
        move.w (a1)+,d0
        move.w (a4),d1
        move.w d0,(a4)+
        cmp.w d1,d0
        beq.s .hnext
        move.l a2,a0
        bhi.s .hgrow
        sub.w d0,d1
        lsl.w #3,d0
        adda.w d0,a0
        move.w d1,d2
        moveq #0,d3
        bra.s .hspan
.hgrow:
        sub.w d1,d0
        lsl.w #3,d1
        adda.w d1,a0
        move.w d0,d2
        moveq #-1,d3
.hspan:
        subq.w #1,d2
.hblock:
Y       set 0
        rept 10
        move.w d3,Y(a0)
Y       set Y+160
        endr
        addq.l #8,a0
        dbf d2,.hblock
.hnext:
        lea 5122(a2),a2
        dbf d7,.hchannel
.done:
        movem.l (sp)+,d2-d7/a2-a6
        rts
PsgDck_DrawEnd:
PsgDck_Rows:
N       set 0
        rept 65
        dc.w N*320
N       set N+1
        endr
        section data
        even
        xdef gPsgDckDraw,gPsgDckPalette
 gPsgDckDraw: dc.l PsgDck_Draw0,PsgDck_Draw1,PsgDck_Draw2,PsgDck_Draw3
 gPsgDckPalette:
        dc.w 0,$700,$070,$770,$007,$707,$077,$777
        dc.w 0,0,0,0,0,0,0,$777
        section bss
        even
        xdef gPsgDckLevels
 gPsgDckLevels: ds.w 3
