#ifndef QEAPP_STUDIO_HOST_CANVAS_H
#define QEAPP_STUDIO_HOST_CANVAS_H
#include "qe/runtime.h"
#include <cstdint>
#include <string>
#include <vector>
class HostCanvas final:public qe::Platform{
public:
    explicit HostCanvas(uint16_t width=240,uint16_t height=320);
    uint16_t width()const override{return width_;}
    uint16_t height()const override{return height_;}
    void pixel(int x,int y,uint16_t c)override;
    void present()override{++present_count_;}
    void reservedSystemKey(qe::KeyEvent ev)override{reserved_.push_back(ev);}
    uint16_t get(int x,int y)const;
    bool savePpm(const std::string& path)const;
    uint32_t presentCount()const{return present_count_;}
    const std::vector<qe::KeyEvent>& reserved()const{return reserved_;}
private:
    uint16_t width_,height_;
    uint32_t present_count_=0;
    std::vector<uint16_t> pixels_;
    std::vector<qe::KeyEvent> reserved_;
};
#endif
