#ifndef __definitions_h
#define __definitions_h

#include <Arduino.h>

#define STEPPER1_DIR_PIN          5
#define STEPPER1_STEP_PIN         2

#define STEPPER2_DIR_PIN          7
#define STEPPER2_STEP_PIN         4

#define ENABLE_PIN                8

#define STEPPER1_HIGH        PORTD |=  0b00000010;
#define STEPPER1_LOW         PORTD &= ~0b00000010;

#define STEPPER2_HIGH        PORTD |=  0b00010000;
#define STEPPER2_LOW         PORTD &= ~0b00010000;

#define TIMER1_INTERRUPTS_ON    TIMSK1 |=  (1 << OCIE1A);
#define TIMER1_INTERRUPTS_OFF   TIMSK1 &= ~(1 << OCIE1A);

#define TIMER3_INTERRUPTS_ON    TIMSK3 |=  (1 << OCIE1A);
#define TIMER3_INTERRUPTS_OFF   TIMSK3 &= ~(1 << OCIE1A);

#define STEPS_PER_MM 2.083333
// #define STEPS_PER_MM 1.8


#define STOP 0
#define RAMP_UP 1
#define RAMP_DOWN 2
#define RUN 3

#define START_INTERVAL 2600
#define MAX_SPEED 120 // 40 max

#endif
