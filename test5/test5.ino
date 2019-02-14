#include <Ethernet.h>
#include <EthernetUdp.h>
#include <ArduinoJson.h>

#define DIR_PIN          7
#define STEP_PIN         4
#define ENABLE_PIN       8

#define STEPPER1_DIR_PIN          5
#define STEPPER1_STEP_PIN         2

#define STEPPER2_DIR_PIN          7
#define STEPPER2_STEP_PIN         4


#define STEP_HIGH        PORTD |=  0b00010010;
#define STEP_LOW         PORTD &= ~0b00010010;

#define TIMER1_INTERRUPTS_ON    TIMSK1 |=  (1 << OCIE1A);
#define TIMER1_INTERRUPTS_OFF   TIMSK1 &= ~(1 << OCIE1A);

#define STEPS_PER_MM 2.083333

#define STOP 0
#define RAMP_UP 1
#define RAMP_DOWN 2
#define RUN 3

typedef struct {
  volatile char dir = 0;
  volatile char nextDir = 0;
  volatile unsigned int maxSpeed = 50; // 40 max
  volatile unsigned long n = 0;
  volatile float d;
  volatile unsigned long stepCount = 0;
  volatile unsigned long nextTotalSteps = 0;
  volatile unsigned long totalSteps = 0;
  volatile int stepPosition = 0;
  volatile unsigned char runningState = STOP;
} RampControlData;

RampControlData rcd;

unsigned int c0;

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(192, 168, 44, 5);
unsigned int localPort = 8888;
EthernetUDP Udp;
char packetBuffer[UDP_TX_PACKET_MAX_SIZE];
StaticJsonBuffer<200> jsonBuffer;

void setup() {
  Ethernet.begin(mac, ip);
  Udp.begin(localPort);
  
  pinMode(STEPPER1_STEP_PIN,   OUTPUT);
  pinMode(STEPPER1_DIR_PIN,    OUTPUT);
  pinMode(STEPPER2_STEP_PIN,   OUTPUT);
  pinMode(STEPPER2_DIR_PIN,    OUTPUT);  
  pinMode(ENABLE_PIN, OUTPUT);

  noInterrupts();
  TCCR1A = 0;
  TCCR1B = 0;
  TCNT1  = 0;
  OCR1A = 50;                             
  TCCR1B |= (1 << WGM12);
  TCCR1B |= ((1 << CS11) | (1 << CS10));
  interrupts();

  Serial1.begin(115200);
  c0 = 5600; // was 2000 * sqrt( 2 * angle / accel )
  c0 = 1600;

  Serial1.println("=========================================================");
  delay(1000); // need this
}



ISR(TIMER1_COMPA_vect)
{
  if ( rcd.stepCount < rcd.totalSteps ) {
    STEP_HIGH
    STEP_LOW
    rcd.stepCount++;
    rcd.stepPosition += rcd.dir;
    
  } else {
    rcd.runningState = STOP;
  }

  switch (rcd.runningState) {
    case STOP:
      if (rcd.nextTotalSteps != 0) {
        rcd.dir = rcd.nextDir;
        rcd.totalSteps = rcd.nextTotalSteps;
        rcd.nextDir = 0;
        rcd.nextTotalSteps = 0;
        digitalWrite(DIR_PIN, rcd.dir < 0 ? HIGH : LOW);
        rcd.runningState = RAMP_UP;
        rcd.n = 0;
        rcd.stepCount = 0;
        rcd.d = c0;

      } else {
        TIMER1_INTERRUPTS_OFF
        Serial1.print("Stopped at: ");
        Serial1.println(rcd.stepPosition);    
      }
    break;
    
    case RAMP_UP:
      rcd.n++;
      rcd.d = rcd.d - (2 * rcd.d) / (4 * rcd.n + 1);
      if ( rcd.d <= rcd.maxSpeed ) { // reached max speed
        rcd.d = rcd.maxSpeed;
        rcd.runningState = RUN;
      }
      
      if ( rcd.n >= rcd.totalSteps - rcd.stepCount ) { // reached halfway point
        rcd.runningState = RAMP_DOWN;  
      }
    break;

    case RUN:
      if ( rcd.stepCount == rcd.totalSteps - rcd.n ) { // switch to the ramp down phase
        rcd.runningState = RAMP_DOWN;  
      }
    break;

    case RAMP_DOWN:
      rcd.n--;
      rcd.d = (rcd.d * (4 * rcd.n + 1)) / (4 * rcd.n + 1 - 2);
    break;
  }

  OCR1A = rcd.d;
}

void moveNSteps(long steps) {
  rcd.nextDir = steps > 0 ? 1 : -1;
  
  if (rcd.runningState != STOP && rcd.nextDir != 0 && rcd.nextDir != rcd.dir) {
    rcd.stepCount = 0;
    rcd.totalSteps = rcd.n;
    rcd.nextTotalSteps = abs(steps) + rcd.n;
    rcd.runningState = RAMP_DOWN;
    
  } else {
    switch (rcd.runningState) {
      case STOP:
        digitalWrite(DIR_PIN, steps < 0 ? HIGH : LOW);
        rcd.dir = steps > 0 ? 1 : -1;
        rcd.totalSteps = abs(steps);
        rcd.d = c0;
        OCR1A = rcd.d;
        rcd.stepCount = 0;
        rcd.n = 0;
        rcd.runningState = RAMP_UP;
       break;
  
      case RAMP_UP:
      case RUN:
        rcd.totalSteps += abs(steps);
      
      case RAMP_DOWN:
        rcd.totalSteps += abs(steps);
        rcd.runningState = RAMP_UP;
        
      break;
    }
  }
  TIMER1_INTERRUPTS_ON
}

void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize) {
    Serial1.println("Received UDP packet");
    Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
    JsonObject& root = jsonBuffer.parseObject(packetBuffer);
    if (root.success()) {
      double dX = root["x"].as<double>();
//      double dY = root["y"].as<double>();
//      double ds1 = (dY + dX) * STEPS_PER_MM;
//      double ds2 = (dY - dX) * STEPS_PER_MM;

      moveNSteps(dX);

      Serial1.println("Moving");
    } else {
      Serial1.println("Failed to decode JSON");
    }

    jsonBuffer.clear();
  }

  
//  for (maxSpeed = 40; maxSpeed < 1000; maxSpeed +=5) {
//    moveToPosition( 18000 );
//    moveToPosition( 0 );
//  }

}
