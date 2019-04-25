#ifndef __RampController_h
#define __RampController_h

#include "definitions.h"

class RampController {
  protected:
    volatile char dir = 0;
    volatile char nextDir = 0;
    volatile unsigned long n = 0;
    volatile float d;
    volatile unsigned long stepCount = 0;
    volatile unsigned long nextTotalSteps = 0;
    volatile unsigned long totalSteps = 0;
    volatile int stepPosition = 0;
    volatile unsigned char runningState = STOP;
    volatile double velocityFactor = 1.0;
  
    virtual void setTimerInterval() = 0;
    virtual void stepPulse() = 0;
    virtual void disableTimerInterrupts() = 0;
    virtual void enableTimerInterrupts() = 0;
    virtual void setDirectionPin(unsigned char value) = 0;

  public:
    void onTimerTick();
    void move(int steps);
    int estimateStepsToGo(int steps);
    void setVelocityFactor(double factor);
};

class RampController1: public RampController {
  protected:
    virtual void setTimerInterval();
    virtual void stepPulse();
    virtual void disableTimerInterrupts();
    virtual void enableTimerInterrupts();
    virtual void setDirectionPin(unsigned char value);
};

class RampController2: public RampController {
  virtual void setTimerInterval();
  virtual void stepPulse();
  virtual void disableTimerInterrupts();
  virtual void enableTimerInterrupts();
  virtual void setDirectionPin(unsigned char value);
};

#endif
