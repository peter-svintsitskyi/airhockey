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

volatile int dir = 0;
volatile int nextDir = 0;
volatile unsigned int maxSpeed = 50; // 40 max
volatile unsigned long n = 0;
volatile float d;
volatile unsigned long stepCount = 0;
volatile unsigned long nextTotalSteps = 0;
volatile unsigned long totalSteps = 0;
volatile int stepPosition = 0;

volatile bool movementDone = false;

volatile unsigned char runningState = 0;

#define STOP 0
#define RAMP_UP 1
#define RAMP_DOWN 2
#define RUN 3

ISR(TIMER1_COMPA_vect)
{
  if ( stepCount < totalSteps ) {
    STEP_HIGH
    STEP_LOW
    stepCount++;
    stepPosition += dir;
  }
  else {
    movementDone = true;
    runningState = STOP;
  }

  switch (runningState) {
    case STOP:
      if (nextTotalSteps != 0) {
        dir = nextDir;
        totalSteps = nextTotalSteps;
        nextDir = 0;
        nextTotalSteps = 0;
        digitalWrite(DIR_PIN, dir < 0 ? HIGH : LOW);
        runningState = RAMP_UP;
        n = 0;
        stepCount = 0;
        d = c0;
//        Serial1.print("Moving opposite direction: ");
//        Serial1.println(totalSteps);
//        Serial1.println(n);
//        Serial1.println(runningState);
      } else {
        TIMER1_INTERRUPTS_OFF
        Serial1.print("Stopped at: ");
        Serial1.println(stepPosition);    
      }
    break;
    
    case RAMP_UP:
      n++;
      d = d - (2 * d) / (4 * n + 1);
      if ( d <= maxSpeed ) { // reached max speed
        d = maxSpeed;
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

  OCR1A = d;
}

void moveNSteps(long steps) {
  nextDir = steps > 0 ? 1 : -1;
  
  if (runningState != STOP && nextDir != 0 && nextDir != dir) {
    stepCount = 0;
    totalSteps = n;
    nextTotalSteps = abs(steps) + n;
    runningState = RAMP_DOWN;
    
  } else {
    switch (runningState) {
      case STOP:
        digitalWrite(DIR_PIN, steps < 0 ? HIGH : LOW);
        dir = steps > 0 ? 1 : -1;
        totalSteps = abs(steps);
        d = c0;
        OCR1A = d;
        stepCount = 0;
        n = 0;
        movementDone = false;
        runningState = RAMP_UP;
       break;
  
      case RAMP_UP:
      case RUN:
        totalSteps += abs(steps);
      
      case RAMP_DOWN:
        totalSteps += abs(steps);
        runningState = RAMP_UP;
        
      break;
    }
  }
  TIMER1_INTERRUPTS_ON
}

void moveToPosition(long p, bool wait = true) {
  moveNSteps(p - stepPosition);
  while ( wait && ! movementDone );
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
