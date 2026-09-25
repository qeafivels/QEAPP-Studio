#include "HostCanvas.h"
#include <fstream>
HostCanvas::HostCanvas(uint16_t w,uint16_t h)
    :width_(w),height_(h),pixels_((size_t)w*h,0){}
void HostCanvas::pixel(int x,int y,uint16_t c){
    if(x>=0&&y>=0&&x<width_&&y<height_)
        pixels_[(size_t)y*width_+(size_t)x]=c;
}
uint16_t HostCanvas::get(int x,int y)const{
    if(x<0||y<0||x>=width_||y>=height_)return 0;
    return pixels_[(size_t)y*width_+(size_t)x];
}
bool HostCanvas::savePpm(const std::string& path)const{
    std::ofstream f(path,std::ios::binary);
    if(!f)return false;
    f<<"P6\n"<<width_<<' '<<height_<<"\n255\n";
    for(const auto p:pixels_){
        const unsigned char rgb[]={
            (unsigned char)(((p>>11)&31)*255/31),
            (unsigned char)(((p>>5)&63)*255/63),
            (unsigned char)((p&31)*255/31)};
        f.write((const char*)rgb,3);
    }
    return (bool)f;
}
