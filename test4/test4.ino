#include "global.h"
#include "sm_driver.h"
#include "steppers.h"


#define STEPPER1_DIR_PIN          5
#define STEPPER1_STEP_PIN         2

#define STEPPER2_DIR_PIN          7
#define STEPPER2_STEP_PIN         4

#define ENABLE_PIN                8

struct GLOBAL_FLAGS status = {FALSE, FALSE, 0};


void setup() {
  pinMode(STEPPER1_STEP_PIN,   OUTPUT);
  pinMode(STEPPER1_DIR_PIN,    OUTPUT);
  pinMode(STEPPER2_STEP_PIN,   OUTPUT);
  pinMode(STEPPER2_DIR_PIN,    OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);

  Serial1.begin(115200);
  Serial1.println("-----------------------------------------------");
  Serial1.println("Setup");
  
  // put your setup code here, to run once:
//  TCCR1A = 0;
//  TCCR1B = 0;
//  TCNT1  = 0;
//  OCR1A = 1000;                             
//  TCCR1B |= (1 << WGM12);
//  TCCR1B |= ((1 << CS11) | (1 << CS10));

  speed_cntr_Init_Timer1();
  delay(1000);
}

void loop() {
  // put your main code here, to run repeatedly:
  Serial1.println("Loop");

  if (!status.running)
    speed_cntr_Move(18000, 800, 800, 2500);
  
  Serial1.println("Done");
  while(true);  
}
