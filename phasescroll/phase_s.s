; Adapted from Jeffrey Young / TheNameOfTheGame, HPSCROLL.S rev 1.01.
; Original phase normalization, fill-gauge and gap compensation retained.
; GodLib owns lifecycle, input, frame sync and raster installation.
        include 'system.equ'
DEBUG equ 0
LM_W equ 144
PF_ROWS equ 10
PF_TLH equ 16
PF_PBH equ 10
PF_MINX equ 0
PF_MAXX equ 1984
ScrAdr          equ 0               ;to enable movep to set video count quickly
ScrAdrH         equ 1               ;--+
ScrAdrM         equ 2               ;--|
ScrAdrL         equ 3               ;--+->screen address for shifter video count
LWidth          equ 4               ;line width offset for shifter fine scroll
HScroll         equ 5               ;hscroll value for shifter fine scroll
Colors          equ 6               ;shifter color palette
LSplit          equ 38              ;line count for timer b raster split

;input structure used in ikbd interrupt to capture user input
KeyScancode     equ 0               ;scancode returned on keypress event
Joy0Header      equ 1               ;header returned on joystick 0 event
Joy0Data        equ 2               ;payload returned on joystick 0 event
Joy1Header      equ 3               ;header returned on joystick 1 event
Joy1Data        equ 4               ;payload returned on joystick 1 event

;playfield structure used to manage phase scrolling
pfScrPtr        equ -4              ;start of visible display in buffer
pfCurrX         equ 0               ;playfield current x-position in pixels
pfSpeed         equ 2               ;scroll speed 0,1,2,4,8,-1,-2,-4,-8
pfDir           equ 4               ;scroll direction offset -1,21
pfFG            equ 6               ;update column fill gauge 1-16
pfCS            equ 8               ;coarse scroll flag -1,0,1
pfLMCurrX       equ 10              ;level map current x-position in tiles
pfPrvSpd        equ 12              ;previous scroll speed 0,1,2,4,8,-1,-2,-4,-8
pfCurrY         equ 14              ;playfield current y-pos in pixels
pfLMCurrY       equ 16              ;level map current y position in tiles


        section text
        xdef Phase_Init,Phase_Step,Phase_StepEnd,Phase_Shifter,Phase_Blitter,Phase_KernelEnd
Phase_Init:
        movem.l d0-d7/a0-a6,-(sp)
        bsr init_blitter
        bsr init_playfield
        movem.l (sp)+,d0-d7/a0-a6
        rts
Phase_Step:
        movem.l d0-d7/a0-a6,-(sp)
        bsr shifter_scroll
        bsr blitter_scroll
        movem.l (sp)+,d0-d7/a0-a6
        rts
Phase_StepEnd:
init_blitter:
            move.w  #2,hw_BLT_SRC_INC_X.w          ;$ff8a20 source x increment
            move.w  #2,hw_BLT_SRC_INC_Y.w          ;$ff8a22 source y increment
            move.l  #$decafbad,hw_BLT_SRC_ADDR_L.w ;$ff8a24 source address
            move.w  #$ffff,hw_BLT_ENDMASK_1.w      ;$ff8a28 endmask 1
            move.w  #$ffff,hw_BLT_ENDMASK_2.w      ;$ff8a2a endmask 2
            move.w  #$ffff,hw_BLT_ENDMASK_3.w      ;$ff8a2c endmask 3
            move.w  #2,hw_BLT_DST_INC_X.w          ;$ff8a2e dest x increment
            move.w  #178,hw_BLT_DST_INC_Y.w        ;$ff8a30 dest y increment
            move.l  Phase_State,hw_BLT_DST_ADDR_L.w   ;$ff8a32 dest address
            move.w  #4,hw_BLT_COUNT_X.w            ;$ff8a36 x count
            move.w  #0,hw_BLT_COUNT_Y.w            ;$ff8a38 y count
            move.b  #2,hw_BLT_HOP.w                ;$ff8a3a hop
            move.b  #3,hw_BLT_OP.w                 ;$ff8a3b op
            move.b  #0,hw_BLT_CONTROL              ;$ff8a3c blitter control
            move.b  #0,hw_BLT_SKEW.w               ;$ff8a3d skew
            rts


init_playfield:
;get pointer into level map
            lea     Phase_Map,a0         ;address of level map
            move.w  pf_lm_cx,d0        ;current level map x-position
            move.w  pf_lm_cy,d1        ;current level map y-position
            mulu.w  #LM_W,d1           ;create y-index down to current y-pos
            add.w   d0,d1              ;move over by x-pos for final index
            add.l   d1,a0              ;adjust pointer to level map current pos
            lea     -1(a0),a0          ;back one column for left update column

;get pointer into playfield buffer
            move.l  pf_scrptr,a2       ;address of playfield screen display
            lea     -8(a2),a2          ;back one column for left update column

;get pointer to tile data and set blitter source
            move.l  Phase_Tiles,a1         ;address of tile graphics data
            move.l  a1,hw_BLT_SRC_ADDR_L.w  ;in 64k block so can use .w in loop

;set loop count
            move.w  #21,d4             ;loop for 22 columns
                                       ;left uc, 20 visible cols, scroll column
;draw playfield columns
.draw_all:  movea.l a0,a5              ;save level map index for next column
            move.w  #PF_ROWS-1,d2      ;loop index for tiles to draw each column
            move.w  a2,hw_BLT_DST_ADDR_L+2.w  ;set blitter destination address
                                              ;to adjusted playfield pointer
                                              ;can use low word of BLT_DST_ADDR
                                              ;as destination is all within 64k
.draw_one:  moveq   #0,d3              ;clear it for byte work
            move.b  (a5),d3            ;copy tile index from level map (0-255)
            lsl.w   #7,d3              ;tile index*128
                                       ;tile graphics each 8 bytes * 16 lines
            movea.l a1,a4              ;address of tile graphics data
            adda.l  d3,a4              ;pointer into tile data for current tile
            move.w  a4,hw_BLT_SRC_ADDR_L+2.w  ;set blitter source address
                                              ;to adjusted tile data address
                                              ;can use low word of BLT_SRC_ADDR
                                              ;as source is all within 64k
            move.w  #PF_TLH,hw_BLT_COUNT_Y.w  ;blitter y-count is tile height
            move.b  #$c0,hw_BLT_CONTROL.w     ;start blitter in HOG mode
            lea     LM_W(a5),a5        ;down in level map for next column tile
            dbf     d2,.draw_one       ;loop until column is done
            lea     1(a0),a0           ;adjust level map index to next column
            lea     8(a2),a2           ;adjust screen address to next column
            dbf     d4,.draw_all       ;loop for all columns
            rts


shifter_scroll:
            lea     pf_currx,a0        ;address register indirect quicker
            moveq   #0,d3              ;coarse scroll flag cleared to start
                                       ;used to flag whether coarse scroll
                                       ;happens and if it is left or right
                                       ;valid flag values are -1,0,1

;handle speed 0
            move.w  pfSpeed(a0),d0     ;current playfield speed +/-
;            beq.s   .get_xpos          ;keep prev speed if current is 0
            beq.s   .cs_done           ;keep prev speed if current is 0
            move.w  d0,pfPrvSpd(a0)    ;prev speed for phase scroll idling
                                       ;if current speed is 0 then prev
                                       ;speed is used to 'idle' so that
                                       ;phase block update keeps the
                                       ;resource use more consistent

;fine scroll range check
.get_xpos:  move.w  pfCurrX(a0),d1     ;current playfield x-position
            move.w  d1,d2              ;to compare if column change later
            add.w   d0,d1              ;change x-pos according to speed +/-
            tst.w   d0                 ;check speed
;            beq.s   .rchk_done         ;if speed = 0, no range check needed
;            bpl.s   .chk_redge         ;if positive, check right edge
            bgt.s   .chk_redge

.chk_ledge: cmp.w   #PF_MINX-1,d1      ;check pos just past left edge
            bgt.s   .rchk_done         ;if not there, then all is ok
            moveq   #PF_MINX,d1        ;otherwise, set x-pos to left edge
            bra.s   .rchk_done         ;and continue

.chk_redge: cmp.w   #PF_MAXX+1,d1      ;check pos just past right edge
            blt.s   .rchk_done         ;if not there, then all is ok
            move.w  #PF_MAXX,d1        ;otherwise, set x-pos to right edge

;coarse scroll check
.rchk_done: move.w  d1,pfCurrX(a0)     ;save new playfield x-position
            andi.w  #$fff0,d1          ;new tile column from current x-pos
            andi.w  #$fff0,d2          ;old tile column from previous x-pos
            cmp.w   d2,d1              ;are the columns different?
            beq.s   .cs_done           ;no, skip coarse scroll adjustment
            bgt.s   .cs_right          ;new column greater so going right

;coarse scroll left
.cs_left:   sub.l   #8,pfScrPtr(a0)    ;adjust playfield screen ptr back
            sub.w   #1,pfLMCurrX(a0)   ;adjust level map ptr back
            moveq   #-1,d3             ;set coarse scroll flag to -1
            tst.w   pfDir(a0)          ;which direction is scroll atm?
            bmi.s   .cs_done           ;already going left so done
            move.w  #-1,pfDir(a0)      ;set new direction
            move.w  #16,pfFG(a0)       ;mark fill gauge as full
            bra.s   .cs_done

;coarse scroll right
.cs_right:  add.l   #8,pfScrPtr(a0)    ;adjust playfield screen ptr forward
            add.w   #1,pfLMCurrX(a0)   ;adjust level map ptr forward
            moveq   #1,d3              ;set coarse scroll flag to 1
            tst.w   pfDir(a0)          ;which direction is scroll atm?
            bpl.s   .cs_done           ;already going right so done
            move.w  #21,pfDir(a0)      ;set new direction
            move.w  #16,pfFG(a0)

;update coarse scroll flag and exit
.cs_done:   move.w  d3,pfCS(a0)        ;update coarse scroll flag
            rts


blitter_scroll:
    IFNE DEBUG
            move.w  #227,hw_VID_COLOR0.w ;rasters enable
    ENDIF
            lea     pf_currx,a0        ;address indirect quicker
            movem.w (a0),d0-d4         ;d0 pf_currx - current x-position
                                       ;d1 pf_speed - scroll speed
                                       ;d2 pf_dir - scroll direction
                                       ;d3 pf_fg - update column fill gauge
                                       ;d4 pf_cs - coarse scroll flag

;handle speed 0
speed0:     tst.w   d1                 ;is speed=0?
            bne.s   normalize          ;no, skip ahead
            move.w  pfPrvSpd(a0),d1    ;yes, use previous non-zero speed
                                       ;this allows smoother 'idling'
            beq     done_bs            ;but if prevspeed was 0, exit

;normalize conditions
normalize:  tst.w   d1                 ;check speed
            bpl.s   .n_ucb             ;positive so skip ahead
.n_speed:   neg.w   d1                 ;normalize speed (absolute)
.n_ucb:     tst.w   d2                 ;check scroll direction
            bpl.s   .n_phase           ;positive so skip ahead
            eor.w   #15,d0             ;normalize update column block 0->15
.n_phase:   moveq   #16,d7             ;for phase masking
            sub.w   d1,d7              ;subtract speed for phase mask
            and.w   d7,d0              ;normalize phase block
                                       ;ex: speed 4 x-pos 4 -> phase block 4
                                       ;    speed 4 x-pos 5 -> phase block 4
                                       ;    speed 4 x-pos 6 -> phase block 4
                                       ;    speed 4 x-pos 7 -> phase block 4

;process fill gauge
fillgauge:  move.w  d0,d7              ;normalized phase block
            add.w   d1,d7              ;get bottom of phase block
            tst.w   d4                 ;was there a coarse scroll?
            beq.s   .no_cs             ;no, skip ahead
            move.w  d7,pfFG(a0)        ;yes, reset fill gauge for new uc
            cmpi.w  #16,d3             ;was previous uc totally filled?
            blt.s   gap_completion     ;no, process the gap
            bra.s   draw_pb            ;yes, no gap so process phase block
.no_cs:     cmp.w   d3,d0              ;is there a gap?
            bgt.s   gap_compensation   ;yes, process the gap
.no_gap:    cmp.w   d3,d7              ;new high water mark?
            ble.s   draw_pb            ;no, process phase block
            move.w  d7,pfFG(a0)        ;yes, save new fill gauge value
            bra.s   draw_pb            ;process phase block

;process gaps
gap_completion:
;-------------------------------------------------------------------------------
;here there was a gap on a previous update column before a coarse scroll
;so we will run a separate draw phase block for the previous update column
;and then come back and do a normal draw phase block.
;-------------------------------------------------------------------------------
            move.w  d0,a4              ;save normalized phase for return
            move.w  d1,a5              ;save normalized speed for return
            move.w  d2,a6              ;save scroll direction for return
            move.w  d3,d0              ;fill gauge is pseudo-phase
            moveq   #16,d1             ;for gap size calc
            sub.w   d3,d1              ;gap size is pseudo-speed
;-------------------------------------------------------------------------------
;normally the update column offset is the same as the scroll direction:
;-1 for left scrolling and 21 for right scrolling
;this is the column offset to draw in the correct column for the direction
;here we need to work on the previous update column so it would change to:
;0 for left scrolling and 20 for right scrolling
;-------------------------------------------------------------------------------
            subq    #1,d2              ;-2 or 20
            tst.w   d2                 ;what scroll direction actually?
            bpl.s   .gap_fill          ;if positive, ready to fill gap
            addq    #2,d2              ;negative, so uc forward to 0
.gap_fill:  bsr     draw_pb            ;process pseudo-phase block
    IFNE DEBUG
            move.w  #227,hw_VID_COLOR0.w ;rasters enable
    ENDIF
            move.w  a4,d0              ;restore normalized phase
            move.w  a5,d1              ;restore normalized speed
            move.w  a6,d2              ;restore scroll direction
            bra.s   draw_pb            ;process phase block

gap_compensation:
;-------------------------------------------------------------------------------
;here there was a gap in the current update column resulting from a fine scroll
;so we will adjust the phase block to account for the gap and drop through to
;normal draw phase block.
;-------------------------------------------------------------------------------
            move.w  d0,d6              ;normalized phase
            move.w  d3,d0              ;new psuedo-phase block
            sub.w   d3,d6              ;gap size
            add.w   d6,d1              ;new psuedo-speed
            add.w   d1,d3              ;new fill gauge value
            move.w  d3,pfFG(a0)        ;save it

;calculate phase block draw parameters
draw_pb:    mulu.w  #PF_PBH,d1         ;lines to draw
            move.w  d0,d4              ;save current phase - needed later
            mulu.w  #PF_PBH,d4         ;line phase starts on
            move.w  d4,d5              ;need both
            lsr.w   #4,d5              ;phase tile number
            andi.w  #$000f,d4          ;phase tile line skip

;get pointer into level map for phase tile
            lea     Phase_Map,a0         ;level map address
            move.w  pf_lm_cx,d6        ;level map current x-pos
            move.w  pf_lm_cy,d7        ;level map current y-pos
            add.w   d5,d7              ;add current phase tile to y-pos
            mulu.w  #LM_W,d7           ;vertical offset into level map
            add.w   d6,d7              ;add horizontal offset
            add.w   d2,d7              ;adjust left or right update column
            adda.l  d7,a0              ;final pointer into level map

;get pointer into tile data for phase tile
            move.l  Phase_Tiles,a1         ;tile data address
            moveq   #0,d7              ;for adda.l below
            move.b  (a0),d7            ;tile index from level map
            lsl.w   #7,d7              ;tiles are 128 bytes each
            move.w  d4,d6              ;phase tile line skip
            lsl.w   #3,d6              ;tile lines are 8 bytes each
            add.w   d6,d7              ;tile data offset
            adda.l  d7,a1              ;final pointer into tile data

;get pointer into playfield buffer for phase tile
            move.l  pf_scrptr,a2       ;current playfield screen pointer
            mulu.w  #184*PF_PBH,d0     ;lines down that phase block starts
            adda.l  d0,a2              ;adjust pointer to phase block start
            ext.l   d2                 ;phase direction is signed
            lsl.l   #3,d2              ;update column offset * 8 bytes
            adda.l  d2,a2              ;final pointer into playfield buffer

;draw phase block tile(s) with blitter
            move.l  a1,hw_BLT_SRC_ADDR_L.w   ;set blitter source address
            move.w  a2,hw_BLT_DST_ADDR_L+2.w ;set blitter destination address
                                             ;to adjusted playfield pointer
                                             ;can use low word of BLT_DST_ADDR
                                             ;as destination is all within 64k
            moveq   #16,d6                   ;tiles are 16 lines high
            sub.w   d4,d6                    ;subtract line skip = lines to draw
.draw_tile: cmp.w   d1,d6                    ;do we have enough lines left?
            ble.s   .blit                    ;yes, blit them
            move.w  d1,d6                    ;no, use what's left

.blit:      move.w  d6,hw_BLT_COUNT_Y.w      ;blitter y-count is lines to draw
            move.b  #$c0,hw_BLT_CONTROL.w    ;start blitter in HOG mod

            sub.w   d6,d1                    ;update lines to draw
            beq.s   done_bs                  ;if no lines left, then exit
            moveq   #16,d6                   ;tiles are 16 lines high
            lea     LM_W(a0),a0              ;next tile location in level map
            move.l  Phase_Tiles,a1               ;tile data address
            moveq   #0,d7                    ;for adda.l below
            move.b  (a0),d7                  ;tile index from level map
            lsl.w   #7,d7                    ;tiles are 128 bytes each
            adda.l  d7,a1                    ;final pointer into tile data
            move.w  a1,hw_BLT_SRC_ADDR_L+2.w ;set blitter source address
                                             ;to adjusted tile data address
                                             ;can use low word of BLT_SRC_ADDR
                                             ;as source is all within 64k
            bra.s   .draw_tile               ;draw next tile
done_bs:
    IFNE DEBUG
            move.w  #$000,hw_VID_COLOR0.w    ;rasters enable
    ENDIF
            rts


Phase_KernelEnd:
Phase_Shifter equ shifter_scroll
Phase_Blitter equ blitter_scroll
        section data
        even
        xdef Phase_State,Phase_Tiles,Phase_Map,Phase_TileAsset,Phase_Palette
Phase_State:
pf_ramptr: dc.l 0
pf_scrptr: dc.l 0
pf_currx: dc.w 192
pf_speed: dc.w 1
pf_dir: dc.w 21
pf_fg: dc.w 0
pf_cs: dc.w 0
pf_lm_cx: dc.w 12
pf_prvspd: dc.w 1
pf_curry: dc.w 352
pf_lm_cy: dc.w 22
Phase_Tiles: dc.l 0
Phase_Palette:
        dc.w $000,$000,$111,$222,$333,$334,$556,$322
        dc.w $f65,$643,$f54,$433,$543,$444,$555,$fff
Phase_Map:
        incbin 'assets/LMAP.BIN'
Phase_TileAsset:
        incbin 'assets/TDATA.BIN'
