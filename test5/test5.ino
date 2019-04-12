#include <Ethernet.h>
#include <EthernetUdp.h>
#include "RampController.h"
#include "definitions.h"

RampController1 stepper1;
RampController2 stepper2;

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(192, 168, 44, 45);
unsigned int localPort = 8888;
EthernetUDP Udp;

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

typedef struct __attribute__((packed)) _UDPPacketType {
  int16_t dx;
  int16_t dy;
  unsigned long counter;
} UDPPacketType;

union {
  UDPPacketType packet;
  unsigned char buffer[sizeof(UDPPacketType)];
} UDPPacket;

void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize) {
    // Serial1.println("Received UDP packet");
    Udp.read(UDPPacket.buffer, 4);

//    Serial1.print("Got packet: ");
//    Serial1.print(UDPPacket.packet.dx);
//    Serial1.print(", ");
//    Serial1.println(UDPPacket.packet.dy);
//    Serial1.println(UDPPacket.packet.counter);
    
    double ds1 = (UDPPacket.packet.dy + UDPPacket.packet.dx) * STEPS_PER_MM;
    double ds2 = (UDPPacket.packet.dy - UDPPacket.packet.dx) * STEPS_PER_MM;

    stepper2.move(ds2);
    stepper1.move(ds1);
    
  }
}
