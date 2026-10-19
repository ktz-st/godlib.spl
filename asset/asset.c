/* Three sources, one AssetClient interface. Relocators own BFB/BSB pointers. */
#include <godlib/asset/asset.h>
#include <godlib/asset/context.h>
#include <godlib/asset/package.h>
#include <godlib/asset/relocate.h>
#include <godlib/font/rel_bfb.h>
#include <godlib/sprite/rel_bsb.h>
#include <godlib/font/font.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/pictypes/degas.h>
#include <godlib/platform/platform.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/screen/screen.h>
#include <godlib/memory/memory.h>
#include <godlib/fade/fade.h>
#include <stdio.h>
#include <string.h>
static sContext context;
static sPackage package;
static sAssetClient clients[4];
static sDegas *picture;static sFont *font,*fontMirror;static sSpriteBlock *sparks;
static U16 active,mode=2,phase;
static U32 baseline;
static U16 fallback[16]={0,0x777};
static const char *names[]={"CASTLE.PI1","FONT.BFB","SPARKS.BSB","FONT.BFB"};
static const char *sources[]={"LOOSE FILES","RAW LINKFILE","GODPACK LINKFILE"};
static const S16 wave[32]={0,3,6,9,11,13,15,16,16,16,15,13,11,9,6,3,0,-3,-6,-9,-11,-13,-15,-16,-16,-16,-15,-13,-11,-9,-6,-3};
volatile U16 gAssetReady,gAssetExited,gAssetMode,gAssetLoaded,gAssetError,gAssetLoads,gAssetUnloads,gAssetReloads,gAssetPointersCleared,gAssetRefCount,gAssetStatus,gAssetFiles,gAssetInside,gAssetEqual,gAssetFlags;
volatile U32 gAssetFrames,gAssetFreeBase,gAssetFreeNow,gAssetLoadCalls[4],gAssetUnloadCalls[4],gAssetHash[3],gAssetReference[3],gAssetStored,gAssetContent,gAssetRawSize;
volatile S32 gAssetFinalRefs;
static U32 hash(U32 state,const void *data,U32 size)
{const U8 *p=(const U8*)data;while(size--)state=((state<<5)|(state>>27))^*p++;return state;}
static U32 spritehash(U32 state,const sSprite *s)
{U32 words=(U32)((s->mWidth+15)>>4)*s->mHeight;state=hash(state,s->mpGfx,words*s->mGfxPlaneCount*2);return hash(state,s->mpMask,words*2);}
static U32 onload(void *data,U32 size,U32 id)
{if(data&&size)++gAssetLoadCalls[id];return data!=0;}
static U32 onunload(void *data,U32 size,U32 id)
{if(data&&size)++gAssetUnloadCalls[id];return 1;}
static U32 freeblock(void){return (U32)GemDos_Malloc(-1L);}
static void snapshot(void)
{
 U16 i;gAssetMode=mode;gAssetLoaded=(picture&&font&&sparks&&fontMirror==font);gAssetRefCount=context.mRefCount;
 gAssetStatus=active?package.mStatus:0;gAssetFreeNow=freeblock();
 if(gAssetLoaded){
  gAssetHash[0]=hash(0,picture,sizeof(sDegas));gAssetHash[1]=0;gAssetHash[2]=0;
  for(i=0;i<font->mSpriteCount;++i)gAssetHash[1]=spritehash(gAssetHash[1],&font->mpSprites[i]);
  for(i=0;i<sparks->mHeader.mSpriteCount;++i)gAssetHash[2]=spritehash(gAssetHash[2],sparks->mpSprite[i]);
  if(!gAssetReference[0])for(i=0;i<3;++i)gAssetReference[i]=gAssetHash[i];
  gAssetFlags=1;for(i=0;i<4;++i)if(!(clients[i].mpAsset->mStatusBits&eASSET_STATUS_BIT_LOADED))gAssetFlags=0;
  if(!(clients[1].mpAsset->mStatusBits&eASSET_STATUS_BIT_RELOCATED)||!(clients[2].mpAsset->mStatusBits&eASSET_STATUS_BIT_RELOCATED))gAssetFlags=0;
  gAssetEqual=1;for(i=0;i<3;++i)if(gAssetHash[i]!=gAssetReference[i])gAssetEqual=0;
 }
}
static void unload(void)
{
 if(active){PackageManager_UnLoad(&package);PackageManager_Update();Package_DeInit(&package);active=0;++gAssetUnloads;}
 gAssetPointersCleared=(!picture&&!font&&!sparks&&!fontMirror);gAssetLoaded=0;gAssetInside=0;Fade_SetPalDirect(fallback);snapshot();
}
static void load(U16 selected)
{
 char path[32];U16 i;U32 start,end;
 unload();mode=selected;gAssetError=0;gAssetFiles=0;
 if(mode==0){for(i=0;i<3;++i){snprintf(path,sizeof(path),"UNLINK\\SCENE\\%s",names[i]);if(!File_Exists(path)){gAssetError=1;return;}}}
 else if(!File_Exists(mode==1?"DATA\\SCENE.LNK":"DATA\\PACKED.LNK")){gAssetError=1;return;}
 PackageManager_SetLinkEnableFlag(mode!=0);PackageManager_SetFilePath("UNLINK");PackageManager_SetLinkPath("DATA");
 Package_Init(&package,mode==2?"PACKED":"SCENE","ASSETDEMO");active=1;
 PackageManager_Load(&package);PackageManager_Update();++gAssetLoads;
 if(!picture||!font||!sparks||fontMirror!=font){gAssetError=2;unload();return;}
 gAssetFiles=package.mFileCount;gAssetContent=clients[0].mpAsset->mSize+clients[1].mpAsset->mSize+clients[2].mpAsset->mSize;
 gAssetStored=mode==0?gAssetContent:(U32)File_GetSize(mode==1?"DATA\\SCENE.LNK":"DATA\\PACKED.LNK");gAssetRawSize=(U32)File_GetSize("DATA\\SCENE.LNK");
 if(mode){start=(U32)package.mpLinkFile;end=start+gAssetRawSize;gAssetInside=((U32)picture>=start&&(U32)picture<end&&(U32)font>=start&&(U32)font<end&&(U32)sparks>=start&&(U32)sparks<end);}
 Screen_GetpBackGraphic()->mpFuncs->CopyScreen(Screen_GetpBackGraphic(),picture->mPixels);Fade_SetPalDirect(picture->mHeader.mPalette);snapshot();
}
static void box(S16 x,S16 y,S16 w,S16 h,U16 colour)
{sGraphicRect r={x,y,w,h};sGraphicCanvas *c=Screen_GetpLogicGraphic();c->mpFuncs->DrawBox(c,&r,colour);}
static void text(const char *s,S16 x,S16 y)
{sGraphicCanvas *c=Screen_GetpLogicGraphic();sGraphicPos pos={x,y};if(font)c->mpClipFuncs->FontPrint(c,&pos,font,s);else Font8x8_Print(s,Screen_GetpLogic(),x,y);}
static void draw(void)
{
 U16 i;char line[40];sGraphicPos pos;sGraphicCanvas *c=Screen_GetpLogicGraphic();
 if(gAssetLoaded){
  c->mpFuncs->CopyScreen(c,Screen_GetpBack());
  for(i=0;i<3;++i){pos.mX=(S16)(32+((phase+i*80)%256));pos.mY=(S16)(90+wave[((phase>>1)+i*10)&31]);c->mpClipFuncs->DrawSprite(c,&pos,sparks->mpSprite[((phase>>2)+i*2)&7]);}
 }else c->mpFuncs->ClearScreen(c);
 box(8,6,304,34,0);text("ASSET / LINKFILE",16,10);snprintf(line,sizeof(line),"%u: %s",mode+1,sources[mode]);text(line,16,26);
 box(8,142,304,58,0);
 if(gAssetLoaded){snprintf(line,sizeof(line),"DISK %lu  DATA %lu  FILES %u",gAssetStored,gAssetContent,gAssetFiles);text(line,16,146);text(gAssetEqual?"SAME ASSETS / AUTO BFB + BSB RELOC":"ASSET CHECK FAILED",16,158);}
 else text(gAssetError?"LOAD FAILED / CHECK DATA FOLDERS":"UNLOADED / ALL CLIENT POINTERS NULL",16,146);
 text("1 LOOSE  2 LNK  3 PACKED",16,172);text("R RELOAD  U UNLOAD  ESC EXIT",16,184);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 i,quit=0;U8 sc;void **dest[4]={(void**)&picture,(void**)&font,(void**)&sparks,(void**)&fontMirror};(void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);Fade_SetPalDirect(fallback);
 PackageManager_Init();RelocaterManager_Init();Relocator_BFB_Init();Relocator_BSB_Init();Context_Init(&context,"ASSETDEMO");
 for(i=0;i<4;++i){clients[i].OnLoad=onload;clients[i].OnUnLoad=onunload;clients[i].mUserData=i;AssetClient_Init(&clients[i],names[i],"ASSETDEMO",dest[i]);}
 baseline=freeblock();gAssetFreeBase=baseline;load(mode);gAssetReady=1;
 while(!quit){
  Screen_Update();IKBD_Update();
  while(IKBD_GetKbdBytesWaiting()){
   sc=IKBD_PopKbdByte();if(sc&0x80)continue;
   if(sc==eIKBDSCAN_ESC)quit=1;
   else if(sc>=eIKBDSCAN_1&&sc<=eIKBDSCAN_3)load((U16)(sc-eIKBDSCAN_1));
   else if(sc==eIKBDSCAN_R){++gAssetReloads;load(mode);}
   else if(sc==eIKBDSCAN_U)unload();
  }
  draw();++phase;++gAssetFrames;
 }
 unload();for(i=4;i>0;--i)AssetClient_DeInit(&clients[i-1]);gAssetFinalRefs=context.mRefCount;Context_DeInit(&context);
 Relocator_BSB_DeInit();Relocator_BFB_DeInit();RelocaterManager_DeInit();PackageManager_DeInit();
 gAssetExited=(gAssetPointersCleared&&gAssetFinalRefs==0&&freeblock()==baseline);
 Screen_DeInit();Platform_DeInit();return gAssetExited?0:1;
}
