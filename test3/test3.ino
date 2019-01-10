#include <Ethernet.h>
#include <EthernetUdp.h>
#include <ArduinoJson.h>

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

#define MAX_SPEED 50
#define ACC_FACTOR 1.2
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
  
  // Udp.begin(localPort);
 
  pinMode(STEPPER1_STEP_PIN,   OUTPUT);
  pinMode(STEPPER1_DIR_PIN,    OUTPUT);
  pinMode(STEPPER2_STEP_PIN,   OUTPUT);
  pinMode(STEPPER2_DIR_PIN,    OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);

  Serial1.begin(115200);

  noInterrupts();
  TCCR1A = 0;
  TCCR1B = 0;
  TCNT1  = 0;
  OCR1A = 1000;                             
  TCCR1B |= (1 << WGM12);
  TCCR1B |= ((1 << CS11) | (1 << CS10));

  TCCR3A = 0;
  TCCR3B = 0;
  TCNT3  = 0;
  OCR3A = 1000;                             
  TCCR3B |= (1 << WGM12);
  TCCR3B |= ((1 << CS11) | (1 << CS10));
  interrupts();

  c0 = 1600; // was 2000 * sqrt( 2 * angle / accel )

  Serial1.println("Done setup.");
}

struct StepperInfo {
  volatile int dir = 0;
  volatile double accFactor = ACC_FACTOR;
  volatile unsigned int maxSpeed = MAX_SPEED;
  volatile unsigned long n = 0;
  volatile float d;
  volatile unsigned long stepCount = 0;
  volatile unsigned long rampUpStepCount = 0;
  volatile unsigned long totalSteps = 0;
  volatile int stepPosition = 0;
  volatile bool movementDone = true;
};

volatile StepperInfo stepper1;
volatile StepperInfo stepper2;

ISR(TIMER1_COMPA_vect)
{
  if ( stepper1.stepCount < stepper1.totalSteps ) {
    STEPPER1_HIGH
    STEPPER1_LOW
    stepper1.stepCount++;
    stepper1.stepPosition += stepper1.dir;
  }
  else {
    stepper1.movementDone = true;
    TIMER1_INTERRUPTS_OFF
  }

  if ( stepper1.rampUpStepCount == 0 ) { // ramp up phase
    stepper1.n++;
    stepper1.d = stepper1.d - (2 * stepper1.d) / (4 * stepper1.n + 1) / stepper1.accFactor;
    if ( stepper1.d <= stepper1.maxSpeed ) { // reached max speed
      stepper1.d = stepper1.maxSpeed;
      stepper1.rampUpStepCount = stepper1.stepCount;
    }
    if ( stepper1.stepCount >= stepper1.totalSteps / 2 ) { // reached halfway point
      stepper1.rampUpStepCount = stepper1.stepCount;
    }
  }
  else if ( stepper1.stepCount >= stepper1.totalSteps - stepper1.rampUpStepCount ) { // ramp down phase
    stepper1.n--;
    stepper1.d = (stepper1.d * (4 * stepper1.n + 1)) / (4 * stepper1.n + 1 - 2);
  }

  OCR1A = stepper1.d;
}

ISR(TIMER3_COMPA_vect)
{
  if ( stepper2.stepCount < stepper2.totalSteps ) {
    STEPPER2_HIGH
    STEPPER2_LOW
    stepper2.stepCount++;
    stepper2.stepPosition += stepper2.dir;
  }
  else {
    stepper2.movementDone = true;
    TIMER3_INTERRUPTS_OFF
  }

  if ( stepper2.rampUpStepCount == 0 ) { // ramp up phase
    stepper2.n++;
    stepper2.d = stepper2.d - (2 * stepper2.d) / (4 * stepper2.n + 1) / stepper2.accFactor;
    if ( stepper2.d <= stepper2.maxSpeed ) { // reached max speed
      stepper2.d = stepper2.maxSpeed;
      stepper2.rampUpStepCount = stepper2.stepCount;
    }
    if ( stepper2.stepCount >= stepper2.totalSteps / 2 ) { // reached halfway point
      stepper2.rampUpStepCount = stepper2.stepCount;
    }
  }
  else if ( stepper2.stepCount >= stepper2.totalSteps - stepper2.rampUpStepCount ) { // ramp down phase
    stepper2.n--;
    stepper2.d = (stepper2.d * (4 * stepper2.n + 1)) / (4 * stepper2.n + 1 - 2);
  }

  OCR3A = stepper2.d;
}

void moveNSteps(long stepper1Steps, long stepper2Steps) {
  digitalWrite(STEPPER1_DIR_PIN, stepper1Steps < 0 ? HIGH : LOW);
  stepper1.dir = stepper1Steps > 0 ? 1 : -1;
  stepper1.totalSteps = abs(stepper1Steps);
  stepper1.d = c0;
  OCR1A = stepper1.d;
  stepper1.stepCount = 0;
  stepper1.n = 0;
  stepper1.rampUpStepCount = 0;
  stepper1.movementDone = false;

  digitalWrite(STEPPER2_DIR_PIN, stepper2Steps < 0 ? HIGH : LOW);
  stepper2.dir = stepper2Steps > 0 ? 1 : -1;
  stepper2.totalSteps = abs(stepper2Steps);
  stepper2.d = c0;
  OCR3A = stepper2.d;
  stepper2.stepCount = 0;
  stepper2.n = 0;
  stepper2.rampUpStepCount = 0;
  stepper2.movementDone = false;
  
  float factor1 = 1.0;
  float factor2 = 1.0;
  float accFactor1 = ACC_FACTOR;
  float accFactor2 = ACC_FACTOR;
  
  if (stepper1.totalSteps > stepper2.totalSteps) {
    factor2 = (float) stepper2.totalSteps / (float)stepper1.totalSteps;
    // stepper2.d = c0 / pow(ACC_FACTOR, factor2);
    // accFactor2 = ACC_FACTOR * pow(1.1, 1 / factor2);
  } else {
    factor1 = (float) stepper1.totalSteps / (float)stepper2.totalSteps;
    // stepper1.d = c0 / pow(ACC_FACTOR, factor1);
    // accFactor1 = ACC_FACTOR * pow(1.1, 1 / factor1);
  }
  
  stepper1.maxSpeed = MAX_SPEED * factor1;
  stepper1.accFactor = accFactor1;
  
  stepper2.maxSpeed = MAX_SPEED * factor2;
  stepper2.accFactor = accFactor2;
  

  TIMER1_INTERRUPTS_ON
  TIMER3_INTERRUPTS_ON
}

void moveToPosition(long p1, long p2, bool wait = true) {
  moveNSteps(p1 - stepper1.stepPosition, p2 - stepper2.stepPosition);
  while ( wait && !stepper1.movementDone && !stepper2.movementDone );
}

void moveAndWait(long steps1, long steps2)
{
  moveNSteps(steps1, steps2);
  while (!stepper1.movementDone || !stepper2.movementDone );
}

bool udpStarted = false;

void loop() {

  if (stepper1.movementDone && stepper2.movementDone) {
    if (!udpStarted) {
      Udp.begin(localPort);
      udpStarted = true;
    }

    
    int packetSize = Udp.parsePacket();
    if (packetSize) {
      Serial1.println("Received UDP packet");
      
      Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
      JsonObject& root = jsonBuffer.parseObject(packetBuffer);
      if (root.success()) {
        double dX = root["x"].as<double>();
        double dY = root["y"].as<double>();
        double ds1 = (dY + dX) * STEPS_PER_MM;
        double ds2 = (dY - dX) * STEPS_PER_MM;

        moveNSteps(ds1, ds2);

        Serial1.println("Moveing");
      } else {
        Serial1.println("Failed to decode JSON");
      }

      jsonBuffer.clear();

      Udp.stop();
      udpStarted = false;
    }
      
  }

//  moveAndWait(1000, 10000);
//   moveAndWait(300, 30000);

//  moveAndWait(300, 0);
//  moveAndWait(-300, 0);
//  moveAndWait(0, 300);
//  moveAndWait(0, -300);
//
//  moveAndWait(300, 1);
//  moveAndWait(-300, -1);
//  moveAndWait(1, 300);
//  moveAndWait(-1, -300);
//
//  moveAndWait(30, 300);
//  moveAndWait(-30, -300);
//
//  moveAndWait(200, 300);
//  moveAndWait(-150, -300);

//  moveAndWait(1000, 20000);
//  moveAndWait(-1000, -20000);
//  
//  moveAndWait(3000, -3000);
//  moveAndWait(-3000, 3000);
//
//  moveAndWait(-3000, 1500);
//  moveAndWait(3000, -1500);
//
//  moveAndWait(-1500, 3000);
//  moveAndWait(1500, -3000);

//  moveAndWait(-1500, 3000);
//  moveAndWait(1500, -3000);
  
//  moveToPosition( -6000 );
//  moveToPosition(  6000 );
//  moveToPosition( -6000 );
  // moveToPosition( 0 );

//  moveToPosition( 200 );
//  moveToPosition( 400 );
//  moveToPosition( 600 );
//  moveToPosition( 800 ); 
//
//  moveToPosition( 400 );
//  moveToPosition( 600 );
//  moveToPosition( 200 );
//  moveToPosition( 400 );
//  moveToPosition( 0 );
//
//  maxSpeed = 600;
//  moveToPosition( 200 );
//  moveToPosition( 400 );
//
//  maxSpeed = 400;
//  moveToPosition( 600 );
//  moveToPosition( 800 );
//
//  maxSpeed = 200;
//  moveToPosition( 1000 );
//  moveToPosition( 1200 );
//
//  maxSpeed = 10;
//  moveToPosition( 0 );

//  while (true);

}
