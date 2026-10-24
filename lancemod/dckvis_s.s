; Five DCK MOD activity-bar styles, adapted to GodLib/GCC fastcall.
; a0=screen, a1=U16 levels[4] (0..16), 4(sp)=previous levels for this page.
; One plane per channel. Per-page deltas only; no source artwork/frame cache.
        section text
        xdef DckModVis_Draw0,DckModVis_Draw1,DckModVis_Draw2
        xdef DckModVis_Draw3,DckModVis_Draw4,DckModVis_DrawEnd
DckModVis_Draw0:
        moveq #0,d0
        bra.s DckModVis_Draw
DckModVis_Draw1:
        moveq #1,d0
        bra.s DckModVis_Draw
DckModVis_Draw2:
        moveq #2,d0
        bra.s DckModVis_Draw
DckModVis_Draw3:
        moveq #3,d0
        bra.s DckModVis_Draw
DckModVis_Draw4:
        moveq #4,d0
DckModVis_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l 48(sp),a4
        cmpi.w #4,d0
        beq.w .horizontal
        lea 168*160+49(a0),a2   ; X=104, low 8px half; subsequent bars X+=32
        lea DckModVis_Rows(pc),a6
        move.w d0,d6
        cmpi.w #2,d6
        seq d5                 ; width16 for style2 or style3
        cmpi.w #3,d6
        seq d4
        or.b d4,d5
        add.w d6,d6
        lea .scale(pc),a0
        move.w 0(a0,d6.w),d6
        moveq #3,d7
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
        bra.s .vspan
.grow:
        move.w d0,d2
        sub.w d1,d2
        add.w d1,d1
        suba.w 0(a6,d1.w),a0
        moveq #-1,d3
.vspan:
        subq.w #1,d2
        tst.b d5
        bne.s .wide
.narrow:
        move.b d3,(a0)
        lea -160(a0),a0
        dbf d2,.narrow
        bra.s .vnext
.wide:
        move.b d3,(a0)
        move.b d3,7(a0)
        lea -160(a0),a0
        dbf d2,.wide
.vnext:
        lea 18(a2),a2           ; X +32px, next channel's plane +2 bytes
        dbf d7,.channel
        bra.w .done
.scale: dc.w 1,2,2,3
.horizontal:
        lea 56*160+16(a0),a2    ; X=32..287, four horizontal 10px rows
        moveq #3,d7
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
        lea 4482(a2),a2         ; +28 rows and next plane
        dbf d7,.hchannel
.done:
        movem.l (sp)+,d2-d7/a2-a6
        rts
DckModVis_DrawEnd:
DckModVis_Rows:
N       set 0
        rept 129
        dc.w N*160
N       set N+1
        endr
        section data
        even
        xdef gDckModVisDraw,gDckModVisPalette
 gDckModVisDraw:
        dc.l DckModVis_Draw0,DckModVis_Draw1,DckModVis_Draw2,DckModVis_Draw3,DckModVis_Draw4
 gDckModVisPalette:
        dc.w 0,$700,$070,$770,$007,$707,$077,$777
        dc.w $077,$777,$777,$777,$777,$777,$777,$777
