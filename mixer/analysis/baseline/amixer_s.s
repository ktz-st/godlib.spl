* Packed biased L/R words (scaled sample + 128); sums cannot carry across words.
* 512-byte clipping table converts each summed component back to signed PCM.
 opt o+
 xref gAudioMixerClip
 xdef AudioMixer_Core,AudioMixer_Lock,AudioMixer_Unlock
AudioMixer_Lock:
 move.w sr,d0
 ori.w #$0700,sr
 rts
AudioMixer_Unlock:
 move.w d0,sr
 rts
* Fastcall a0: voices.l, destination.l, frame count.w, source steps0/1.w.
* Voice layout: start0,current4,end8,length12,gainL16,gainR17,volume18,
* active19,pan20,repeat21,phase22,table24; size28.
AudioMixer_Core:
 movem.l d2-d7/a2-a6,-(sp)
 move.l (a0),a6
 move.l 4(a0),a1
 move.w 8(a0),d6
 beq .done
 subq.w #1,d6
 move.l 4(a6),a2
 move.l 32(a6),a3
 move.l 24(a6),a4
 move.l 52(a6),a5
 move.w 22(a6),d4
 move.w 50(a6),d5
 move.w 10(a0),d3
 move.w 12(a0),d7
 lea gAudioMixerClip,a0
 cmp.w #1,d3
 bne.s .loop
 cmp.w #1,d7
 bne.s .loop
 cmp.b #1,21(a6)
 bne.s .loop
 cmp.b #1,49(a6)
 bne.s .loop
.fast:
 moveq #0,d0
 move.b (a2)+,d0
 lsl.w #2,d0
 move.l (a4,d0.w),d1
 moveq #0,d0
 move.b (a3)+,d0
 lsl.w #2,d0
 add.l (a5,d0.w),d1
 move.w d1,d2
 swap d1
 move.b (a0,d1.w),(a1)+
 move.b (a0,d2.w),(a1)+
 dbra d6,.fast
 bra.s .save
.loop:
 moveq #0,d0
 move.b (a2),d0
 lsl.w #2,d0
 move.l (a4,d0.w),d1
 moveq #0,d0
 move.b (a3),d0
 lsl.w #2,d0
 add.l (a5,d0.w),d1
 move.w d1,d2
 swap d1
 move.b (a0,d1.w),(a1)+
 move.b (a0,d2.w),(a1)+
 subq.w #1,d4
 bne.s .next1
 adda.w d3,a2
 moveq #0,d4
 move.b 21(a6),d4
.next1:
 subq.w #1,d5
 bne.s .next
 adda.w d7,a3
 moveq #0,d5
 move.b 49(a6),d5
.next:
 dbra d6,.loop
.save:
 move.l a2,4(a6)
 move.l a3,32(a6)
 move.w d4,22(a6)
 move.w d5,50(a6)
.done:
 movem.l (sp)+,d2-d7/a2-a6
 rts
