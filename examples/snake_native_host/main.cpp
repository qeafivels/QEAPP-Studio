#include "SnakeDemo.h"
#include "HostCanvas.h"
#include "qe/runtime.h"
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
int main(int argc,char** argv){
    std::string output,scenario="playing";
    unsigned frames=90;
    for(int i=1;i<argc;++i){
        const std::string a=argv[i];
        if(a=="--out"&&i+1<argc)output=argv[++i];
        else if(a=="--scenario"&&i+1<argc)scenario=argv[++i];
        else if(a=="--frames"&&i+1<argc) {
            const std::string n=argv[++i];
            if(n.empty()||n.find_first_not_of("0123456789")!=std::string::npos)return 2;
            frames=(unsigned)std::strtoul(n.c_str(),nullptr,10);
        }else{std::cerr<<"Invalid argument: "<<a<<'\n';return 2;}
    }
    if(output.empty()||(scenario!="ready"&&scenario!="playing"&&scenario!="paused")||frames>2000){
        std::cerr<<"Usage: snake_host --out file.ppm --scenario ready|playing|paused --frames 0..2000\n";
        return 2;
    }
    HostCanvas canvas;
    SnakeDemo game;
    qe::Runtime runtime(game,canvas);
    if(!runtime.start(0))return 3;
    if(scenario=="playing"||scenario=="paused"){
        runtime.queue({qe::Key::Ok,qe::KeyAction::Press});
        runtime.tick(0);
    }
    if(scenario=="paused") {
        runtime.queue({qe::Key::Ok,qe::KeyAction::Press});
        runtime.tick(0);
    }
    for(unsigned t=1;t<=frames;++t){
        // Deterministic path bounded by walls; previews are generated at 40 ticks.
        if(scenario=="playing"){
            if(t==8)runtime.queue({qe::Key::Down,qe::KeyAction::Press});
            if(t==16)runtime.queue({qe::Key::Left,qe::KeyAction::Press});
            if(t==26)runtime.queue({qe::Key::Up,qe::KeyAction::Press});
            if(t==40)runtime.queue({qe::Key::Right,qe::KeyAction::Press});
        }
        runtime.tick(t*50u);
    }
    if(!canvas.savePpm(output)){std::cerr<<"Unable to write screenshot\n";return 4;}
    std::cout<<"HOST_ONLY scenario="<<scenario<<" frames="<<frames
             <<" updates="<<runtime.stats().updates<<" renders="<<runtime.stats().renders
             <<" dropped_ms="<<runtime.stats().dropped_ms<<" input_overflows="<<runtime.stats().input_overflows
             <<" score="<<game.score()<<" game_over="<<game.gameOver()<<'\n';
    runtime.stop();
    return 0;
}
