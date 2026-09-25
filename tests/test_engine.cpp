#include "qe/runtime.h"
#include "HostCanvas.h"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
using namespace qe;
class FakeApp final:public App {
public:
    int initialized=0,updated=0,drawn=0,inputs=0,pauses=0,resumes=0,stops=0;
    uint32_t last_dt=0;
    void init(Platform&)override{++initialized;}
    void update(uint32_t dt)override{++updated;last_dt=dt;}
    void draw(Platform&)override{++drawn;}
    void onKey(KeyEvent)override{++inputs;}
    void pause()override{++pauses;}
    void resume()override{++resumes;}
    void shutdown()override{++stops;}
};
static void test_draw_bounds(){
    HostCanvas canvas(20,16);
    fillRect(canvas,-4,-4,7,7,0xffff);
    for(int y=0;y<16;++y)for(int x=0;x<20;++x)
        assert(canvas.get(x,y)==((x<3&&y<3)?0xffff:0));
    fillRect(canvas,18,14,INT32_MAX,INT32_MAX,0x1234);
    assert(canvas.get(19,15)==0x1234);
    assert(canvas.get(3,3)==0);
    fillRect(canvas,0,0,-1,3,3);
    assert(canvas.get(1,1)==0xffff);
    border(canvas,2,2,1,1,0xf800);
    assert(canvas.get(2,2)==0xf800);
    const uint16_t sprite_pixels[]={1,2,3,4};
    const Sprite565 invalid{sprite_pixels,3,2,2,0,false};
    assert(!sprite(canvas,0,0,invalid));
    const Sprite565 valid{sprite_pixels,4,2,2,1,true};
    assert(sprite(canvas,0,0,valid));
    assert(canvas.get(0,0)==0xffff); // transparency leaves old pixel
    assert(canvas.get(1,0)==2);
    assert(canvas.get(0,1)==3);
    assert(canvas.get(1,1)==4);
    smallText(canvas,-6,4,"HI",0x7bef,3); // test clipping only
}
static void test_runtime(){
    FakeApp game; HostCanvas canvas(240,320);
    Runtime engine(game,canvas);
    assert(engine.start(10));assert(!engine.start(10));
    assert(game.initialized==1&&game.drawn==1&&canvas.presentCount()==1);
    assert(engine.queue({Key::Up,KeyAction::Press}));
    engine.tick(35);assert(game.updated==0&&game.inputs==1);
    engine.tick(60);assert(game.updated==1&&game.last_dt==50);
    engine.tick(260);assert(game.updated==5); // 4-step limit catches up
    engine.tick(5000);assert(engine.stats().dropped_ms>=4000); // clamp
    assert(!engine.queue({Key::Menu,KeyAction::Press}));
    assert(!engine.queue({Key::SelectLong,KeyAction::Release}));
    assert(canvas.reserved().size()==2);assert(game.inputs==1);
    for(unsigned i=0;i<Runtime::INPUT_CAPACITY;++i)
        assert(engine.queue({Key::Left,KeyAction::Press}));
    assert(!engine.queue({Key::Right,KeyAction::Press}));
    assert(engine.stats().input_overflows==1);
    engine.tick(5000);assert(game.inputs==1+Runtime::INPUT_CAPACITY);
    engine.pause(); assert(engine.paused());assert(game.pauses==1);
    assert(!engine.queue({Key::Up,KeyAction::Press}));
    engine.tick(10000);assert(engine.stats().updates==9);
    engine.resume(10000);assert(game.resumes==1);
    engine.tick(10050);assert(engine.stats().updates==10);
    engine.stop();engine.stop();assert(game.stops==1);
    assert(!engine.queue({Key::Down,KeyAction::Press}));
}
static void test_clock_wrap_and_invalid_config(){
    FakeApp game;HostCanvas canvas;
    Runtime invalid(game,canvas,Config{240,320,0,4}); assert(!invalid.start(0));
    Runtime bad_view(game,canvas,Config{320,240,50,4});assert(!bad_view.start(0));
    Runtime r(game,canvas);
    assert(r.start(UINT32_MAX-24));
    r.tick(25); // unsigned wrap gives 50ms elapsed
    assert(game.updated==1);
    r.stop();
}
int main(){
    test_draw_bounds();
    test_runtime();
    test_clock_wrap_and_invalid_config();
    std::cout<<"PASS test_engine: draw/clipping, lifecycle, fixed step, reserved keys, overflow, pause/resume, millis wrap\n";
}
