#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#include <stdio.h>
extern void Xor_Init(void),Xor_Advance(void),Xor_Erase(void),Xor_Draw(void);
U16 gXorStars[256][3],gXorLists[2][256][2];
U16 *gXorSaved;
U8 *gXorScreen,*gXorBack;
volatile U16 gXorCount=256,gXorMode,gXorOldCount,gXorPaused,gXorRaster,gXorReady,gXorExited;
volatile U32 gXorFrames,gXorMissedVbl;
#ifdef XOR_BENCH
volatile U16 gXorHold,gXorRequest,gXorCompleted;
volatile U32 gXorCalls;
#endif
static void Header(sGraphicCanvas *c)
{
    static const char *names[]={"RIGHT","LEFT ","DOWN ","UP   "};
    sGraphicRect r={0,16,320,8};char text[40];
    GraphicCanvas_DrawBox(c,&r,0);
    sprintf(text,"%s   %u STARS   SPEEDS 1 TO 4",names[gXorMode],gXorCount);
    Font8x8_PrintColourCanvas(text,c,8,16,7);
}
static void Background(sGraphicCanvas *c)
{
    static const U16 colours[6]={0,1,4,1,0,4};sGraphicRect r;U16 i;
    GraphicCanvas_ClearScreen(c);
    Font8x8_PrintColourCanvas("DCK XOR STARS - FOUR DIRECTIONS",c,40,2,7);
    r.mX=0;r.mWidth=320;r.mHeight=24;
    for(i=0;i<6;++i){r.mY=28+i*24;GraphicCanvas_DrawBox(c,&r,colours[i]);}
    Font8x8_PrintColourCanvas("1 RIGHT  2 LEFT  3 DOWN  4 UP",c,40,176,7);
    Font8x8_PrintColourCanvas("5 64 STARS   6 128   7 256",c,48,184,7);
    Font8x8_PrintColourCanvas("SPACE PAUSE  R CPU  ESC EXIT",c,48,192,7);
    Header(c);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    static U16 pal[16]={0,0x012,0x777,0x567,0x102,0x123,0x767,0x777,0,0,0,0,0,0,0,0};
    U16 quit=0,page,counts[2]={0,0},dirty[2]={0,0};U32 last=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Xor_Init();Background(Screen_GetpBackGraphic());
    GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
    GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());
    gXorBack=(U8*)Screen_GetpBack();Video_SetPalST(pal);gXorReady=1;
    while(!quit){
#ifdef XOR_BENCH
        if(gXorHold){
            if(gXorRequest){U16 request=gXorRequest,n,iterations=request==2?1:32;gXorRequest=0;gXorCalls=0;
                for(n=0;n<iterations;++n){Xor_Erase();Xor_Advance();Xor_Draw();gXorOldCount=gXorCount;++gXorCalls;}
                gXorCompleted=request;
            }
            continue;
        }
#endif
        Screen_Update();
        {U32 now=Vbl_GetCounter();if(last && now-last>1)gXorMissedVbl+=now-last-1;last=now;}
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()){
            U8 k=IKBD_PopKbdByte();U16 changed=0;
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gXorPaused^=1;
            if(k==eIKBDSCAN_R)gXorRaster^=1;
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_4){gXorMode=k-eIKBDSCAN_1;changed=1;}
            if(k==eIKBDSCAN_RIGHTARROW){gXorMode=0;changed=1;}
            if(k==eIKBDSCAN_LEFTARROW){gXorMode=1;changed=1;}
            if(k==eIKBDSCAN_DOWNARROW){gXorMode=2;changed=1;}
            if(k==eIKBDSCAN_UPARROW){gXorMode=3;changed=1;}
            if(k>=eIKBDSCAN_5 && k<=eIKBDSCAN_7){gXorCount=(U16)(64U<<(k-eIKBDSCAN_5));changed=1;}
            if(changed){Header(Screen_GetpBackGraphic());dirty[0]=dirty[1]=1;}
        }
        page=Screen_GetLogicIndex();
        if(dirty[page]){Header(Screen_GetpLogicGraphic());dirty[page]=0;}
        gXorScreen=(U8*)Screen_GetpLogic();gXorSaved=&gXorLists[page][0][0];gXorOldCount=counts[page];
        if(gXorRaster)*(volatile U16*)0xffff8240UL=0x070;
        Xor_Erase();if(!gXorPaused)Xor_Advance();Xor_Draw();counts[page]=gXorCount;
        if(gXorRaster)*(volatile U16*)0xffff8240UL=0;
        ++gXorFrames;
    }
    Screen_DeInit();Platform_DeInit();gXorExited=1;return 0;
}
