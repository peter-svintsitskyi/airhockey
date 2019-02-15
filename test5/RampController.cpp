#include "RampController.h"

// ================== STEPPER 1 ==============================

inline void RampController1::setTimerInterval() {
  OCR1A = d;
}

inline void RampController1::stepPulse() {
  STEPPER1_HIGH;
  STEPPER1_LOW;
}

inline void RampController1::disableTimerInterrupts() {
  TIMER1_INTERRUPTS_OFF
}

inline void RampController1::enableTimerInterrupts() {
  TIMER1_INTERRUPTS_ON
}

inline void RampController1::setDirectionPin(unsigned char value) {
  digitalWrite(STEPPER1_DIR_PIN, value);
}

// ================== STEPPER 2 ==============================

void RampController2::setTimerInterval() {
  OCR3A = d;
}

void RampController2::stepPulse() {
  STEPPER2_HIGH;
  STEPPER2_LOW;
}

void RampController2::disableTimerInterrupts() {
  TIMER3_INTERRUPTS_OFF
}

void RampController2::enableTimerInterrupts() {
  TIMER3_INTERRUPTS_ON
}

void RampController2::setDirectionPin(unsigned char value) {
  digitalWrite(STEPPER2_DIR_PIN, value);
}

// ================== BASE ====================================

void RampController::onTimerTick() {
  if ( stepCount < totalSteps ) {
    stepPulse();
    stepCount++;
    stepPosition += dir;
    
  } else {
    runningState = STOP;
  }

  switch (runningState) {
    case STOP:
      if (nextTotalSteps != 0) {
        dir = nextDir;
        totalSteps = nextTotalSteps;
        nextDir = 0;
        nextTotalSteps = 0;
        setDirectionPin(dir < 0 ? HIGH : LOW);
        runningState = RAMP_UP;
        n = 0;
        stepCount = 0;
        d = START_INTERVAL;

      } else {
        disableTimerInterrupts();
        Serial1.print("Stopped at: ");
        Serial1.println(stepPosition);    
      }
    break;
    
    case RAMP_UP:
      n++;
      d = d - (2 * d) / (4 * n + 1);
      if ( d <= MAX_SPEED ) { // reached max speed
        d = MAX_SPEED;
        runningState = RUN;
      }
      
      if ( n >= totalSteps - stepCount ) { // reached halfway point
        runningState = RAMP_DOWN;  
      }
    break;

    case RUN:
      if ( stepCount == totalSteps - n ) { // switch to the ramp down phase
        runningState = RAMP_DOWN;  
      }
    break;

    case RAMP_DOWN:
      n--;
      d = (d * (4 * n + 1)) / (4 * n + 1 - 2);
    break;
  }

  setTimerInterval();  
}

void RampController::move(long steps) {
  nextDir = steps > 0 ? 1 : -1;
  
  if (runningState != STOP && nextDir != 0 && nextDir != dir) {
    stepCount = 0;
    totalSteps = n;
    nextTotalSteps = abs(steps) + n;
    runningState = RAMP_DOWN;
    
  } else {
    switch (runningState) {
      case STOP:
        setDirectionPin(steps < 0 ? HIGH : LOW);
        dir = steps > 0 ? 1 : -1;
        totalSteps = abs(steps);
        d = START_INTERVAL;
        OCR1A = d;
        stepCount = 0;
        n = 0;
        runningState = RAMP_UP;
       break;
  
      case RAMP_UP:
      case RUN:
        totalSteps = abs(steps);
        stepCount = 0;
      
      case RAMP_DOWN:
        totalSteps = abs(steps);
        stepCount = 0;
        runningState = RAMP_UP;
        
      break;
    }
  }
  
  enableTimerInterrupts();
}
