#ifndef QEAPP_STUDIO_SNAKE_DEMO_H
#define QEAPP_STUDIO_SNAKE_DEMO_H
#include "qe/runtime.h"
#include <array>
#include <cstdint>
class SnakeDemo final: public qe::App {
public:
    void init(qe::Platform&)override;
    void update(uint32_t)override;
    void draw(qe::Platform&)override;
    void onKey(qe::KeyEvent)override;
    void pause()override{os_paused_=true;}
    void resume()override{os_paused_=false;}
    void shutdown()override{started_=false;}
    int score()const{return score_;}
    bool gameOver()const{return game_over_;}
private:
    struct Cell{int8_t x=0,y=0;};
    static constexpr int W=16,H=18,CAP=W*H;
    std::array<Cell,CAP> body_{};
    int length_=0,dx_=1,dy_=0,pending_dx_=1,pending_dy_=0;
    int food_x_=12,food_y_=9;
    int score_=0,high_=0;
    uint32_t rng_=0xA7B3C9D1u;
    uint32_t step_ms_=0;
    bool started_=false,game_over_=false,user_paused_=false,os_paused_=false;
    void restart();
    void placeFood();
    void move();
    bool occupies(int x,int y,int checked_length)const;
};
#endif
