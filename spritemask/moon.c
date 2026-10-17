#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/sprite/sprite.h>
#include <godlib/system/system.h>
#include <godlib/video/video.h>

typedef struct { U32 offset; U16 rows,words; } sMoonDirty;
extern U8 Moon_Image[],Moon_Foreground[],Moon_Phases[];
extern U16 Moon_Palette[];
extern S16 Moon_Path[918][2];
extern void Moon_Render(void);
extern U8 Star_Frames[];
extern U16 Star_Positions[4][3];
sSprite gStarSprites[4][3];
volatile U16 gStarTick,gStarDrawTick;
static void Stars_Restore(void)
{
    U16 i;
    for(i=0;i<4;++i) {
        sGraphicPos pos;sGraphicRect rect;
        pos.mX=rect.mX=Star_Positions[i][0];pos.mY=rect.mY=Star_Positions[i][1];
        rect.mWidth=16;rect.mHeight=16;
        Screen_Logic_Blit_Clip(&pos,&rect,Screen_GetpBackGraphic());
    }
}
static void Stars_Draw(void)
{
    U16 i;gStarDrawTick=gStarTick;
    for(i=0;i<4;++i) {
        U16 phase=(gStarDrawTick+Star_Positions[i][2])%192;
        U16 frame=phase<8 ? 0 : phase<16 ? 1 : phase<24 ? 2 : phase<32 ? 1 : 0;
        sGraphicPos pos;pos.mX=Star_Positions[i][0];pos.mY=Star_Positions[i][1];
        Screen_Logic_DrawSprite_Clip(&pos,&gStarSprites[i][frame]);
    }
}
U8 *gMoonScreen,*gMoonBackground,*gMoonSprite,*gMoonForeground;
sMoonDirty gMoonOld[2],*gMoonDirty;
U16 gMoonWorkGfx[48*4*4],gMoonWorkMask[48*4];
sSprite gMoonGodSprite;
volatile U16 gMoonUsingBlitter;
volatile S16 gMoonX,gMoonY;
volatile U16 gMoonStep,gMoonPaused,gMoonRows,gMoonWords,gMoonColourSkip,gMoonMaskSkip,gMoonSpriteSkip,gMoonReady,gMoonExited;
volatile U32 gMoonOffset,gMoonFrames,gMoonLastVbl,gMoonMissedVbl;

S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0,i;(void)argc;(void)argv;
    GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    gMoonBackground=(U8*)Screen_GetpBack();
    Memory_Copy(32000,Moon_Image,gMoonBackground);
    GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),gMoonBackground);
    GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),gMoonBackground);
    gMoonGodSprite.mpGfx=gMoonWorkGfx;gMoonGodSprite.mpMask=gMoonWorkMask;
    gMoonGodSprite.mWidth=64;gMoonGodSprite.mGfxPlaneCount=4;gMoonGodSprite.mMaskPlaneCount=4;
    for(i=0;i<12;++i) {
        sSprite *star=&gStarSprites[i/3][i%3];
        star->mpMask=(U16*)(Star_Frames+i*160);
        star->mpGfx=(U16*)(Star_Frames+i*160+32);
        star->mWidth=16;star->mHeight=16;
        star->mGfxPlaneCount=4;star->mMaskPlaneCount=4;
    }
    Graphic_SetBlitterEnable(BLT_BLITTER);
    gMoonUsingBlitter=System_GetBLT()==BLT_BLITTER;
    Video_SetPalST(Moon_Palette);gMoonReady=1;
    while(!quit) {
        U32 now;Screen_Update();now=Vbl_GetCounter();
        if(gMoonFrames && now-gMoonLastVbl>1)gMoonMissedVbl+=now-gMoonLastVbl-1;
        gMoonLastVbl=now;IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE){gMoonStep=0;gStarTick=0;}
            if(k==eIKBDSCAN_P)gMoonPaused^=1;
        }
        gMoonX=Moon_Path[gMoonStep][0];gMoonY=Moon_Path[gMoonStep][1];
        {
            S16 top=gMoonY<0 ? 0 : gMoonY;
            S16 bottom=gMoonY+48;
            U16 sourceRow=gMoonY<0 ? -gMoonY : 0;
            if(bottom>200)bottom=200;
            gMoonRows=bottom>top && gMoonX<320 ? bottom-top : 0;
            gMoonWords=gMoonRows ? (320-(gMoonX&~15))>>4 : 0;
            if(gMoonWords>4)gMoonWords=4;
            gMoonOffset=gMoonRows ? (U32)(U16)top*160UL+(gMoonX>>4)*8 : 0;
            gMoonColourSkip=160-gMoonWords*8;
            gMoonMaskSkip=40-gMoonWords*2;
            gMoonSpriteSkip=40-gMoonWords*10;
            gMoonSprite=Moon_Phases+(U32)(gMoonX&15)*1920UL;
            gMoonForeground=Moon_Foreground;
            if(gMoonRows) {
                gMoonSprite+=(U32)sourceRow*40UL;
                gMoonForeground+=(U32)(U16)top*40UL+(gMoonX>>4)*2;
            }
        }
        gMoonScreen=(U8*)Screen_GetpLogic();gMoonDirty=&gMoonOld[Screen_GetLogicIndex()];
        Stars_Restore();
        Moon_Render(); /* restore old page, then cut foreground out of work sprite */
        Stars_Draw();
        if(gMoonRows) {
            sGraphicPos pos;
            pos.mX=gMoonX&~15;pos.mY=gMoonY<0 ? 0 : gMoonY;
            gMoonGodSprite.mHeight=gMoonRows;
            Screen_Logic_DrawSprite_Clip(&pos,&gMoonGodSprite);
        }
        gMoonDirty->offset=gMoonOffset;gMoonDirty->rows=gMoonRows;gMoonDirty->words=gMoonWords;
        ++gMoonFrames;
        if(!gMoonPaused) {
            if(++gMoonStep==918)gMoonStep=0;
            if(++gStarTick==192)gStarTick=0;
        }
    }
    Screen_DeInit();Platform_DeInit();gMoonExited=1;return 0;
}
