; Snowfall algorithm by Jason J Railton, ICTARI, 12 December 1996.
; GodLib adaptation: sparse-word scan and all-down fast path.
; Fixed ST low resolution layout: 320x200, stride 160.
        section text
        xdef Snow_Step,Snow_StepEnd
        xref gSnowScreen
Snow_Step:
        movem.l d0-d7/a0-a2,-(sp)
        move.l gSnowScreen,a1
        lea 31838(a1),a1
        move.w #3979,d0
.scan:
        move.w (a1),d1
        beq .next
        lea 154(a1),a2          ; four-plane group directly below
        move.w (a2),d3
        or.w 2(a2),d3
        or.w 4(a2),d3
        or.w 6(a2),d3
        move.w d3,d5
        not.w d5
        and.w d1,d5
        or.w d5,d3
        or.w d5,6(a2)
        not.w d5
        and.w d5,d1
        beq .all_down
        ; Only blocked flakes need diagonal neighbour masks.
        move.w -8(a2),d2
        or.w -6(a2),d2
        or.w -4(a2),d2
        or.w -2(a2),d2
        moveq #-1,d4
        cmp.w #3979,d0          ; no read past last screen group
        beq .diagonal
        move.w 8(a2),d4
        or.w 10(a2),d4
        or.w 12(a2),d4
        or.w 14(a2),d4
.diagonal:
	swap	d1		;Move some down and to the right...
	clr.w	d1
	ror.l	#1,d1

	swap	d3
	move.w	d4,d3		;This is the only change from the first
*				;block.  This uses the mask from below
*				;the snow (d3) with the same mask from
*				;the previous cycle (d4).

	move.l	d3,d5
	not.l	d5
	and.l	d1,d5

	move.l	d5,d6

	or.l	d5,d3
	or.w	d5,14(a2)
	swap	d5
	or.w	d5,6(a2)

	not.l	d6
	and.l	d6,d1


	swap	d1		;Down and to the left...
	rol.l	#2,d1

	move.w	d2,d3
	swap	d3

	move.l	d3,d5
	not.l	d5
	and.l	d1,d5

	move.l	d5,d6

	or.l	d5,d3
	or.w	d5,6(a2)
	swap	d5
	or.w	d5,-2(a2)

	not.l	d6
	and.l	d6,d1
	ror.l	#1,d1
	move.w	d1,(a1)		;What's left goes back on screen.


.next:
        subq.l #8,a1
        dbf d0,.scan
        movem.l (sp)+,d0-d7/a0-a2
        rts
.all_down:
        clr.w (a1)
        bra .next
Snow_StepEnd:
        section data
        even
        xdef Snow_Background
Snow_Background:
        incbin 'assets/WINTER.BIN'
