/* Even-length ASCII stream; a second NUL permits Griff pair lookahead. */
const char gTinyText[] = "  Siemka! GodLib compares MCoder and Griff: two fast 8x8 scrollers on a plain Atari ST.  Same font, same text, 2 pixels per frame.  ABC xyz gypq 0123456789 !?  Greetings to all ST and STE coders!     " "\0";
const U16 gTinyTextLength=sizeof(gTinyText)-2;
typedef char TinyEvenText[((sizeof(gTinyText)-2)&1)?-1:1];
