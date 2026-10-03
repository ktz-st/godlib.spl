#include <godlib/graphic/graphic.h>
#include <godlib/sprite/sprite.h>
#include <string.h>
#define W 384
#define H 32
static U16 buffer[W*H/4+2],reference[W*H/4+2],gfx[1280];
static U8 colour(U16 x,U16 y) { return (x+y)&15; }
static void put(U16 *p,U16 x,U16 y,U8 c)
{
 U16 i,mask=0x8000U>>(x&15);p+=y*(W/4)+(x>>4)*4;
 for(i=0;i<4;++i) p[i]=(p[i]&~mask)|((c&(1U<<i))?mask:0);
}
volatile U16 gSpriteTestPhase=0xffff;
U16 HScroll_VerifySprites(void)
{
 sGraphicCanvas canvas; sSprite *sprite; U16 *mask;
 U16 mode,phase,x,y,p; sGraphicPos pos;
 memset(gfx,0,sizeof(gfx));
 for(y=0;y<16;++y) for(x=0;x<16;++x)
  for(p=0;p<4;++p) if(colour(x,y)&(1<<p)) gfx[y*80+p]|=0x8000U>>x;
 mask=Sprite_MaskCreate(gfx,16,16,4,4,0);
 sprite=Sprite_Create(gfx,mask,16,16,4,4,0);
 if(!mask || !sprite) return 1;
 GraphicCanvas_Init(&canvas,eGRAPHIC_COLOURMODE_4PLANE,W,H);
 canvas.mpVRAM=buffer+1;
 for(mode=0;mode<2;++mode) {
  Graphic_SetBlitterEnable(mode);
  for(phase=0;phase<35;++phase) {
   gSpriteTestPhase=mode*40+phase;
   pos.mX=phase<32?phase:(phase==32?-7:W-8);
   pos.mY=phase==34?H-8:(phase==32?-4:8);
   memset(buffer,0xa5,sizeof(buffer));memcpy(reference,buffer,sizeof(buffer));
   for(y=0;y<16;++y) for(x=0;x<16;++x) {
    S16 dx=pos.mX+x,dy=pos.mY+y;U8 c=colour(x,y);
    if(c && dx>=0 && dx<W && dy>=0 && dy<H) put(reference+1,dx,dy,c);
   }
   canvas.mpClipFuncs->DrawSprite(&canvas,&pos,sprite);
   if(memcmp(buffer,reference,sizeof(buffer))) {
    GraphicCanvas_DeInit(&canvas);Sprite_Destroy(sprite);Sprite_MaskDestroy(mask);
    return 100+mode*40+phase;
   }
  }
 }
 GraphicCanvas_DeInit(&canvas);Sprite_Destroy(sprite);Sprite_MaskDestroy(mask);
 return 0;
}
