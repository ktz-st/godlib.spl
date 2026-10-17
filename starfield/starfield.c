/* demOS starfield by J.Hubert (2015-2022), adapted for GodLib / GCC ELF.
 * MIT license: see LICENSE.demOS. Projection and generated pixel routines
 * follow FX/STARFILD/STARFILD.C and STARFILD.S. */
#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#define WIDTH 320
#define HEIGHT 152
#define TOP 24
#define MAX_STARS 768
extern void Stars_Draw(void),Stars_Erase(void);
extern U16 Stars_Code[],Stars_Pix0[],Stars_Pix1[];
extern U8 Stars_Loop[],Stars_Reset[];
U16 gStarsPreX[320L*128],gStarsPreY[152L*128],gStarsOffsets[320*8+1];
U16 *gStarsZ[MAX_STARS*2],*gStarsRandomX[512],*gStarsRandomY[497];
U16 **gStarsCurrentX=gStarsRandomX,**gStarsCurrentY=gStarsRandomY;
U8 *gStarsEraseLists[2][MAX_STARS],**gStarsErase,*gStarsScreen;
U16 gStarsEraseCount,gStarsOldCount[2];
volatile U16 gStarsCount=192,gStarsPaused,gStarsReady,gStarsExited,gStarsInitError;
volatile U32 gStarsFrames,gStarsLastVbl,gStarsMissedVbl;
U32 gStarsCodeBytes;
static U32 gSeed=0x31415926UL;
static U16 StarsRandom(void)
{
    gSeed^=gSeed<<13;gSeed^=gSeed>>17;gSeed^=gSeed<<5;
    return (U16)(gSeed>>8);
}
static U16 Generate(void)
{
    U16 *code=Stars_Code,x,c,p;S32 branch;
    for(x=0;x<WIDTH;++x) {
        U16 group=(x&0xfff0)>>1,bit=x&7;
        if(x&8)++group;
        gStarsOffsets[x*8]=(U32)code-(U32)Stars_Code;
        for(c=1;c<7;++c) {
            gStarsOffsets[x*8+c]=(U32)code-(U32)Stars_Code;
            if(group){*code++=0x45ea;*code++=group;} /* lea group(a2),a2 */
            *code++=0x26ca; /* move.l a2,(a3)+: save GROUP base, not first plane */
            for(p=0;p<3;++p)if(c&(1<<p)) {
                if(!p)*code++=Stars_Pix0[bit];
                else {*code++=Stars_Pix1[bit*2];*code++=p*2;}
            }
            *code++=0x51c8; /* dbra d0,Stars_Loop */
            branch=(S32)(U32)Stars_Loop-(S32)(U32)code;
            if(branch < -32768L || branch>32767L)return 0;
            *code++=(U16)branch;*code++=0x4e75;
        }
        gStarsOffsets[x*8+7]=gStarsOffsets[x*8+6];
    }
    gStarsCodeBytes=(U32)code-(U32)Stars_Code;
    branch=(S32)(U32)Stars_Reset-(S32)(U32)Stars_Code;
    if(gStarsCodeBytes>32768UL || branch < -32768L || branch>32767L)return 0;
    gStarsOffsets[WIDTH*8]=(U16)branch;
    return 1;
}
static U16 InitField(void)
{
    U16 t,z;
    if(!Generate())return 0;
    for(t=0;t<WIDTH;++t)for(z=0;z<128;++z) {
        S16 x=(((S32)t-160)*32)/(127-z+21)+160;
        U16 c=z/21+1;
        gStarsPreX[(U32)t*128+z]=gStarsOffsets[x>=0 && x<WIDTH && z!=127 ? x*8+c : WIDTH*8];
    }
    for(t=0;t<HEIGHT;++t)for(z=0;z<128;++z) {
        S16 y=(((S32)t-HEIGHT/2)*32)/(127-z+32)+HEIGHT/2;
        gStarsPreY[(U32)t*128+z]=y*160;
    }
    for(t=0;t<511;++t)gStarsRandomX[t]=gStarsPreX+(U32)(StarsRandom()%WIDTH)*128;
    for(t=0;t<496;++t)gStarsRandomY[t]=gStarsPreY+(U32)(StarsRandom()%HEIGHT)*128;
    for(t=0;t<MAX_STARS;++t) {
        U16 x=StarsRandom()%WIDTH,y=StarsRandom()%HEIGHT,d=StarsRandom()&127;
        gStarsZ[t*2]=gStarsPreX+(U32)x*128+d;
        gStarsZ[t*2+1]=gStarsPreY+(U32)y*128+d;
    }
    return 1;
}
static void Prepare(void)
{
    static U16 pal[16]={0,0x111,0x222,0x333,0x444,0x555,0x777,0x777,
                          0x367,0x367,0x367,0x367,0x367,0x367,0x367,0x367};
    sGraphicCanvas *c=Screen_GetpBackGraphic();
    GraphicCanvas_ClearScreen(c);
    Font8x8_PrintColourCanvas("GODLIB / DEMOS STARFIELD",c,64,8,8);
    Font8x8_PrintColourCanvas("1:96  2:192  3:384  4:768",c,64,184,8);
    Font8x8_PrintColourCanvas("SPACE PAUSE       ESC EXIT",c,56,192,8);
    GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
    GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());Video_SetPalST(pal);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    if(!InitField()) {gStarsInitError=1;Screen_DeInit();Platform_DeInit();return 1;}
    Prepare();gStarsReady=1;
    while(!quit) {
        U32 now;U16 wasPaused=gStarsPaused;
        if(gStarsPaused)Vbl_WaitVbl();else Screen_Update();
        now=Vbl_GetCounter();
        if(gStarsFrames && !wasPaused && now-gStarsLastVbl>1)gStarsMissedVbl+=now-gStarsLastVbl-1;
        gStarsLastVbl=now;IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gStarsPaused^=1;
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_4)gStarsCount=96<<(k-eIKBDSCAN_1);
        }
        if(!gStarsPaused && !quit) {
            U16 index=Screen_GetLogicIndex();
            gStarsScreen=(U8*)Screen_GetpLogic()+TOP*160;
            gStarsErase=gStarsEraseLists[index];
            if(gStarsOldCount[index]) {
                gStarsEraseCount=gStarsOldCount[index]/6-1;Stars_Erase();
            }
            Stars_Draw();gStarsOldCount[index]=gStarsCount;++gStarsFrames;
        }
    }
    Screen_DeInit();Platform_DeInit();gStarsExited=1;return 0;
}
