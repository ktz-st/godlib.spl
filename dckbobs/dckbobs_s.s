; DCK trajectory bobs with GodLib's ordinary sprite and chunk-list APIs.
; GCC -mshort -mfastcall: pointers a0/a1, third pointer at 4(sp).
        section text
        xdef Bobs_Init,Bobs_InitEnd,Bobs_Advance,Bobs_AdvanceEnd
        xdef Bobs_Restore,Bobs_RestoreEnd,Bobs_Draw,Bobs_DrawEnd
        xdef Bobs_Store,Bobs_StoreEnd,Bobs_Frame,Bobs_FrameEnd,Bobs_Seed
        xref gBobsPositions,gBobsPrevious,gBobsIndices,gBobsCount,gBobsPath
        xref gBobsPaused,gBobsTrails,gBobsCanvas,gBobsBackCanvas,gBobsList,gBobsDrawFn
        xref Graphic_ChunkList_ReStore,Graphic_ChunkList_Store
Bobs_Init:
        movem.l d2-d7/a2-a6,-(sp)
        lea gBobsIndices,a3
        moveq #0,d0
        moveq #7,d7
.index: move.w d0,(a3)+
        addi.w #12*4,d0
        dbf d7,.index
        bsr .positions
        lea gBobsPositions,a0
        lea gBobsPrevious,a1
        rept 8
        move.l (a0)+,(a1)+
        endr
        movem.l (sp)+,d2-d7/a2-a6
        rts
.positions:
        move.w gBobsPath,d0
        add.w d0,d0
        lea Bobs_Lengths,a0
        move.w 0(a0,d0.w),d6
        lsl.w #2,d6
        add.w d0,d0
        lea Bobs_Paths,a0
        move.l 0(a0,d0.w),a2
        lea gBobsIndices,a3
        lea gBobsPositions,a4
        moveq #7,d7
.point: move.w (a3)+,d0
        move.l 0(a2,d0.w),(a4)+
        dbf d7,.point
        rts
Bobs_InitEnd:
Bobs_Advance:
        movem.l d2-d7/a2-a4,-(sp)
        lea gBobsPositions,a0
        lea gBobsPrevious,a1
        rept 8
        move.l (a0)+,(a1)+
        endr
        tst.w gBobsPaused
        bne.s .done
        move.w gBobsPath,d0
        add.w d0,d0
        lea Bobs_Lengths,a0
        move.w 0(a0,d0.w),d6
        lsl.w #2,d6
        add.w d0,d0
        lea Bobs_Paths,a0
        move.l 0(a0,d0.w),a2
        lea gBobsIndices,a3
        lea gBobsPositions,a4
        moveq #7,d7
.next:  move.w (a3),d0
        addq.w #4,d0
        cmp.w d6,d0
        blo.s .nowrap
        sub.w d6,d0
.nowrap:move.w d0,(a3)+
        move.l 0(a2,d0.w),(a4)+
        dbf d7,.next
.done:  movem.l (sp)+,d2-d7/a2-a4
        rts
Bobs_AdvanceEnd:
Bobs_Restore:
        tst.w gBobsTrails
        bne.s .done
        move.l gBobsCanvas,-(sp)
        move.l gBobsList,a0
        move.l gBobsBackCanvas,a1
        jsr Graphic_ChunkList_ReStore
        addq.l #4,sp
.done:  rts
Bobs_RestoreEnd:
Bobs_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        tst.w gBobsTrails
        beq.s .current
        ; This page missed the previous frame: stamp it first, then the new one.
        ; Both pages therefore retain every global frame, in identical order.
        lea gBobsPrevious,a3
        bsr Bobs_DrawAll
.current:
        lea gBobsPositions,a3
        bsr Bobs_DrawAll
        movem.l (sp)+,d2-d7/a2-a6
        rts
Bobs_DrawAll:
        lea Bobs_SpritePointers,a4
        move.w gBobsCount,d7
        subq.w #1,d7
.bob:   move.l (a4)+,-(sp)
        move.l gBobsCanvas,a0
        move.l a3,a1
        move.l gBobsDrawFn,a2
        jsr (a2)                ; GodLib Graphic_4BP_DrawSprite[_BLT]
        addq.l #4,sp
        addq.l #4,a3
        dbf d7,.bob
        rts
Bobs_DrawEnd:
Bobs_Seed:
        movem.l d2-d7/a2-a6,-(sp)
        lea gBobsPositions,a3
        bsr Bobs_DrawAll
        movem.l (sp)+,d2-d7/a2-a6
        rts
Bobs_Store:
        tst.w gBobsTrails
        bne.s .done
        movem.l d2-d7/a2-a6,-(sp)
        lea gBobsPositions,a3
        move.w gBobsCount,d7
        subq.w #1,d7
.next:  move.l (a3)+,Bobs_Rect
        lea Bobs_Rect,a0
        move.l a0,-(sp)
        move.l gBobsList,a0
        move.l gBobsCanvas,a1
        jsr Graphic_ChunkList_Store
        addq.l #4,sp
        dbf d7,.next
        movem.l (sp)+,d2-d7/a2-a6
.done:  rts
Bobs_StoreEnd:
Bobs_Frame:
        bsr Bobs_Restore
        bsr Bobs_Advance
        bsr Bobs_Draw
        bsr Bobs_Store
        rts
Bobs_FrameEnd:
        section data
        even
        xdef Bobs_Palette,Bobs_Sprites,Bobs_Paths,Bobs_Lengths,Bobs_PathData
Bobs_Palette: incbin "assets/PALETTE.BIN"
Bobs_Sprites:
        dc.l Bobs_SpriteData,Bobs_SpriteData+432
        dc.w 32,27,4,4
        dc.l Bobs_SpriteData+540,Bobs_SpriteData+972
        dc.w 32,27,4,4
        dc.l Bobs_SpriteData+1080,Bobs_SpriteData+1512
        dc.w 32,27,4,4
Bobs_SpritePointers:
        dc.l Bobs_Sprites,Bobs_Sprites+16,Bobs_Sprites+32
        dc.l Bobs_Sprites,Bobs_Sprites+16,Bobs_Sprites+32
        dc.l Bobs_Sprites,Bobs_Sprites+16
Bobs_SpriteData: incbin "assets/SPRITES.BIN"
        include "assets/paths.inc"
Bobs_PathData: incbin "assets/PATHS.BIN"
Bobs_Rect: dc.w 0,0,32,27
