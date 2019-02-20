#include <Ethernet.h>
#include <EthernetUdp.h>
#include <ArduinoJson.h>
#include "RampController.h"
#include "definitions.h"

RampController1 stepper1;
RampController2 stepper2;

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(192, 168, 44, 45);
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

  TCCR3A = 0;
  TCCR3B = 0;
  TCNT3  = 0;
  OCR3A = 50;                             
  TCCR3B |= (1 << WGM12);
  TCCR3B |= ((1 << CS11) | (1 << CS10));
  interrupts();

  Serial1.begin(115200);
  Serial1.println("======================= DONE SET UP ==================================");
  
  delay(1000); // need this
}

ISR(TIMER1_COMPA_vect)
{
  stepper1.onTimerTick();
}

ISR(TIMER3_COMPA_vect)
{
  stepper2.onTimerTick();
}

void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize) {
    // Serial1.println("Received UDP packet");
    Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
    JsonObject& root = jsonBuffer.parseObject(packetBuffer);
    if (root.success()) {
      double dX = root["x"].as<double>();
      double dY = root["y"].as<double>();
      double ds1 = (dY + dX) * STEPS_PER_MM;
      double ds2 = (dY - dX) * STEPS_PER_MM;

      stepper1.move(ds1);
      stepper2.move(ds2);

      // Serial1.println("Moving");
    } else {
      Serial1.println("Failed to decode JSON");
    }

    jsonBuffer.clear();
  }
}
