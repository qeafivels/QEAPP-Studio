/* Native interactive application sample: HOST ONLY until firmware has an
 * independent app runtime. Reuses exactly the same Platform/Runtime as Snake.
 */
#include "HostCanvas.h"
#include "qe/runtime.h"
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
class HelloApp final:public qe::App{
    int pressed_=0,color_index_=0;
    bool os_paused_=false;
    static constexpr uint16_t colors_[4]={0xFFE0,0x07FF,0xF81F,0xFBE0};
public:
    void init(qe::Platform&)override{pressed_=color_index_=0;}
    void update(uint32_t)override{}
    void draw(qe::Platform& d)override{
        qe::fillRect(d,0,0,240,320,0x1082);
        qe::fillRect(d,0,0,240,28,0x1384);
        qe::smallText(d,12,9,"VQEAF HOST APP",0xffff,2);
        qe::smallText(d,30,46,"HELLO QEAPP",0xAFE5,3);
        qe::smallText(d,30,86,"HOST PREVIEW",0xffff,2);
        qe::fillRect(d,31,111,178,120,0x2104);
        qe::border(d,31,111,178,120,0xFFFF);
        qe::fillRect(d,61,137,118,52,colors_[color_index_]);
        qe::smallText(d,61,198,"COUNT",0xFFFF,2);
        char buf[8];int n=0,v=pressed_;
        do{buf[n++]=(char)('0'+v%10);v/=10;}while(v&&n<7);
        for(int i=0;i<n/2;++i){char c=buf[i];buf[i]=buf[n-1-i];buf[n-1-i]=c;}
        buf[n]=0;
        qe::smallText(d,108,198,buf,0xffff,2);
        if(os_paused_)qe::smallText(d,65,246,"OS PAUSE",0xF800,2);
        qe::smallText(d,13,276,"OK COUNT",0xffff,2);
        qe::smallText(d,13,295,"OPTION COLOR",0xFBE0,2);
    }
    void onKey(qe::KeyEvent ev)override{
        if(ev.action!=qe::KeyAction::Press)return;
        if(ev.key==qe::Key::Ok && pressed_<9999)++pressed_;
        else if(ev.key==qe::Key::Option)color_index_=(color_index_+1)%4;
        else if(ev.key==qe::Key::Back)pressed_=0;
    }
    void pause()override{os_paused_=true;}
    void resume()override{os_paused_=false;}
    void shutdown()override{}
};
int main(int argc,char** argv){
    std::string output,scenario="playing";unsigned frames=40;
    for(int i=1;i<argc;++i){
        const std::string a=argv[i];
        if(a=="--out"&&i+1<argc)output=argv[++i];
        else if(a=="--scenario"&&i+1<argc)scenario=argv[++i];
        else if(a=="--frames"&&i+1<argc){
            const std::string n=argv[++i];
            if(n.empty()||n.find_first_not_of("0123456789")!=std::string::npos)return 2;
            frames=(unsigned)std::strtoul(n.c_str(),nullptr,10);
        }else return 2;
    }
    if(output.empty()||(scenario!="ready"&&scenario!="playing"&&scenario!="paused")||frames>2000)return 2;
    HostCanvas canvas;HelloApp app;qe::Runtime run(app,canvas);
    if(!run.start(0))return 3;
    if(scenario=="playing"){
        run.queue({qe::Key::Ok,qe::KeyAction::Press});
        run.queue({qe::Key::Option,qe::KeyAction::Press});
    } else if(scenario=="paused")run.pause();
    for(unsigned i=1;i<=frames;++i)run.tick(i*50u);
    if(!canvas.savePpm(output))return 4;
    std::cout<<"HOST_ONLY demo=hello scenario="<<scenario<<" updates="<<run.stats().updates
             <<" renders="<<run.stats().renders<<" dropped_ms="<<run.stats().dropped_ms
             <<" input_overflows="<<run.stats().input_overflows<<'\n';
    run.stop();return 0;
}
