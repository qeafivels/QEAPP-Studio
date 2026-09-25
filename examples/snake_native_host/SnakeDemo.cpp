#include "SnakeDemo.h"
#include <algorithm>
namespace {
constexpr uint16_t C_BG=0x1263,C_BOARD=0x0841,C_GRID=0x1082,C_WHITE=0xffff;
constexpr uint16_t C_GREEN=0x4FEA,C_HEAD=0xAFE5,C_FOOD=0xF8A5,C_GOLD=0xFE02;
constexpr int CELL=12,X0=24,Y0=51;
}
void SnakeDemo::init(qe::Platform&){restart();started_=false;}
void SnakeDemo::restart(){
    length_=4;dx_=pending_dx_=1;dy_=pending_dy_=0;
    for(int i=0;i<length_;++i)body_[i]={(int8_t)(8-i),(int8_t)9};
    food_x_=12;food_y_=9;score_=0;step_ms_=0;
    game_over_=false;user_paused_=false;started_=true;
}
bool SnakeDemo::occupies(int x,int y,int check)const{
    for(int i=0;i<check;++i)if(body_[i].x==x&&body_[i].y==y)return true;
    return false;
}
void SnakeDemo::placeFood(){
    if(length_>=CAP){game_over_=true;return;}
    for(int i=0;i<CAP*2;++i){
        rng_^=rng_<<13;rng_^=rng_>>17;rng_^=rng_<<5;
        const int x=(rng_>>8)%W,y=(rng_>>16)%H;
        if(!occupies(x,y,length_)){food_x_=x;food_y_=y;return;}
    }
    for(int y=0;y<H;++y)for(int x=0;x<W;++x)
        if(!occupies(x,y,length_)){food_x_=x;food_y_=y;return;}
}
void SnakeDemo::move(){
    dx_=pending_dx_;dy_=pending_dy_;
    const int nx=body_[0].x+dx_,ny=body_[0].y+dy_;
    const bool eating=nx==food_x_&&ny==food_y_;
    const int collision_body_length=length_-(eating?0:1);
    if(nx<0||nx>=W||ny<0||ny>=H||occupies(nx,ny,collision_body_length)){
        game_over_=true;return;
    }
    if(eating&&length_<CAP){++length_;score_+=10;high_=std::max(high_,score_);}
    for(int i=length_-1;i>=1;--i)body_[i]=body_[i-1];
    body_[0]={(int8_t)nx,(int8_t)ny};
    if(eating)placeFood();
}
void SnakeDemo::update(uint32_t dt){
    if(!started_||game_over_||user_paused_||os_paused_)return;
    step_ms_+=dt;
    if(step_ms_>=150){step_ms_-=150;move();}
}
void SnakeDemo::onKey(qe::KeyEvent ev){
    if(ev.action!=qe::KeyAction::Press)return;
    if(ev.key==qe::Key::Ok){
        if(!started_||game_over_)restart();
        else user_paused_=!user_paused_;
        return;
    }
    if(!started_||game_over_||user_paused_)return;
    int x=0,y=0;
    if(ev.key==qe::Key::Up)y=-1;
    else if(ev.key==qe::Key::Down)y=1;
    else if(ev.key==qe::Key::Left)x=-1;
    else if(ev.key==qe::Key::Right)x=1;
    else return;
    // Opposite turns are forbidden relative to actual heading AND pending heading.
    if((x==-dx_&&y==-dy_)||(x==-pending_dx_&&y==-pending_dy_))return;
    pending_dx_=x;pending_dy_=y;
}
void SnakeDemo::draw(qe::Platform& d){
    qe::fillRect(d,0,0,d.width(),d.height(),C_BG);
    qe::fillRect(d,0,0,240,27,0x2382);qe::smallText(d,10,9,"VQEAF  PIXEL SNAKE",C_WHITE,2);
    qe::smallText(d,24,34,"SCORE",C_GOLD,2);qe::smallText(d,100,34,"HI",C_GOLD,2);
    char scores[8];char high[8];
    const auto toDigits=[](unsigned v,char out[8]) {
        char buf[8];int n=0;
        do{buf[n++]=(char)('0'+v%10);v/=10;}while(v&&n<7);
        int i=0;while(n)out[i++]=buf[--n];out[i]=0;
    };
    toDigits(score_,scores);toDigits(high_,high);
    qe::smallText(d,70,34,scores,C_WHITE,2);qe::smallText(d,130,34,high,C_WHITE,2);
    qe::fillRect(d,X0-3,Y0-3,W*CELL+6,H*CELL+6,C_GRID);
    qe::fillRect(d,X0,Y0,W*CELL,H*CELL,C_BOARD);
    for(int y=0;y<H;++y)for(int x=0;x<W;++x)
        if((x+y)&1)qe::fillRect(d,X0+x*CELL,Y0+y*CELL,CELL,CELL,0x10A2);
    for(int i=length_-1;i>=0;--i){
        const int sx=X0+body_[i].x*CELL,sy=Y0+body_[i].y*CELL;
        qe::fillRect(d,sx+1,sy+1,CELL-2,CELL-2,i==0?C_HEAD:C_GREEN);
        if(i==0){
            qe::fillRect(d,sx+3,sy+3,2,2,C_BOARD);
            qe::fillRect(d,sx+7,sy+3,2,2,C_BOARD);
        }
    }
    const int fx=X0+food_x_*CELL,fy=Y0+food_y_*CELL;
    qe::fillRect(d,fx+3,fy+2,6,7,C_FOOD);
    qe::fillRect(d,fx+6,fy+1,2,3,C_GREEN);
    if(!started_||game_over_||user_paused_){
        qe::fillRect(d,31,119,178,70,0x2124);qe::border(d,31,119,178,70,C_GOLD);
        if(game_over_)qe::smallText(d,42,132,"GAME OVER",C_WHITE,3);
        else if(user_paused_)qe::smallText(d,61,132,"PAUSED",C_WHITE,3);
        else qe::smallText(d,65,132,"READY",C_WHITE,3);
        qe::smallText(d,51,163,"PRESS OK",C_GOLD,2);
    }
    qe::smallText(d,18,285,"D PAD MOVE",C_WHITE,2);
    qe::smallText(d,18,301,"OK START PAUSE",C_GOLD,2);
}
