#include "qe/runtime.h"
#include <algorithm>
#include <cstdint>
namespace qe {
void fillRect(PixelSink& dst,int x,int y,int w,int h,uint16_t color){
    if(w<=0||h<=0)return;
    // Convert to int64 before adding to avoid overflow on malformed assets.
    const int64_t x0=std::max<int64_t>(0,x),y0=std::max<int64_t>(0,y);
    const int64_t x1=std::min<int64_t>(dst.width(),(int64_t)x+w);
    const int64_t y1=std::min<int64_t>(dst.height(),(int64_t)y+h);
    for(int64_t yy=y0;yy<y1;++yy)
        for(int64_t xx=x0;xx<x1;++xx)dst.pixel((int)xx,(int)yy,color);
}
void border(PixelSink& dst,int x,int y,int w,int h,uint16_t color){
    if(w<=0||h<=0)return;
    fillRect(dst,x,y,w,1,color);
    const int64_t bottom=(int64_t)y+h-1;
    if(h>1 && bottom>=INT32_MIN && bottom<=INT32_MAX)
        fillRect(dst,x,(int)bottom,w,1,color);
    const int64_t inside=(int64_t)y+1;
    if(h>2 && inside>=INT32_MIN && inside<=INT32_MAX){
        fillRect(dst,x,(int)inside,1,h-2,color);
        const int64_t right=(int64_t)x+w-1;
        if(w>1 && right>=INT32_MIN && right<=INT32_MAX)
            fillRect(dst,(int)right,(int)inside,1,h-2,color);
    }
}
bool sprite(PixelSink& dst,int x,int y,const Sprite565& s){
    if(!s.pixels||s.width==0||s.height==0||s.width>256||s.height>256||
       (size_t)s.width*s.height>s.pixel_count)return false;
    for(int yy=0; yy<(int)s.height; ++yy){
        const int64_t dy=(int64_t)y+yy;
        if(dy<0||dy>=dst.height())continue;
        for(int xx=0; xx<(int)s.width;++xx){
            const int64_t dx=(int64_t)x+xx;
            if(dx<0||dx>=dst.width())continue;
            const auto c=s.pixels[(size_t)yy*s.width+xx];
            if(!s.has_transparency||c!=s.transparent_color)
                dst.pixel((int)dx,(int)dy,c);
        }
    }
    return true;
}
/* Small 3x5 pixel ASCII glyphs; no heap allocation/fonts on the device.
 * Characters outside the table become blank. Letter patterns row-major.
 */
static void glyph(char c, uint8_t out[5]){
    struct G {char c;uint8_t rows[5];};
    static constexpr G glyphs[]={
        {'A',{2,5,7,5,5}},{'B',{6,5,6,5,6}},{'C',{3,4,4,4,3}},
        {'D',{6,5,5,5,6}},{'E',{7,4,6,4,7}},{'F',{7,4,6,4,4}},
        {'G',{3,4,5,5,3}},{'H',{5,5,7,5,5}},{'I',{7,2,2,2,7}},
        {'J',{1,1,1,5,2}},{'K',{5,5,6,5,5}},{'L',{4,4,4,4,7}},
        {'M',{5,7,7,5,5}},{'N',{5,7,7,7,5}},{'O',{2,5,5,5,2}},
        {'P',{6,5,6,4,4}},{'Q',{2,5,5,7,3}},{'R',{6,5,6,5,5}},
        {'S',{3,4,2,1,6}},{'T',{7,2,2,2,2}},{'U',{5,5,5,5,7}},
        {'V',{5,5,5,5,2}},{'W',{5,5,7,7,5}},{'X',{5,5,2,5,5}},
        {'Y',{5,5,2,2,2}},{'Z',{7,1,2,4,7}},
        {'0',{7,5,5,5,7}},{'1',{2,6,2,2,7}},{'2',{6,1,2,4,7}},
        {'3',{6,1,2,1,6}},{'4',{5,5,7,1,1}},{'5',{7,4,6,1,6}},
        {'6',{3,4,7,5,7}},{'7',{7,1,2,2,2}},{'8',{7,5,7,5,7}},
        {'9',{7,5,7,1,6}},{':',{0,2,0,2,0}},{'-',{0,0,7,0,0}},
        {'!',{2,2,2,0,2}},{'.',{0,0,0,0,2}},{'/',{1,1,2,4,4}},
        {' ',{0,0,0,0,0}}};
    if(c>='a'&&c<='z')c=(char)(c-'a'+'A');
    for(const auto& g:glyphs)if(g.c==c){for(int r=0;r<5;++r)out[r]=g.rows[r];return;}
    for(int r=0;r<5;++r)out[r]=0;
}
void smallText(PixelSink& dst,int x,int y,const char* text,uint16_t color,int scale){
    if(!text||scale<1||scale>4)return;
    for(int pos=0;pos<120&&text[pos];++pos){
        uint8_t rows[5];glyph(text[pos],rows);
        for(int r=0;r<5;++r)for(int col=0;col<3;++col){
            const int64_t px=(int64_t)x+(int64_t)pos*4*scale+col*scale;
            const int64_t py=(int64_t)y+r*scale;
            if((rows[r]&(1<<(2-col))) && px>=INT32_MIN && px<=INT32_MAX
                && py>=INT32_MIN && py<=INT32_MAX)
                fillRect(dst,(int)px,(int)py,scale,scale,color);
        }
    }
}
}
