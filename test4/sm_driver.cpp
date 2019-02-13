/*This file has been prepared for Doxygen automatic documentation generation.*/
/*! \file *********************************************************************
 *
 * \brief Stepper motor driver.
 *
 * Stepper motor driver, increment/decrement the position and outputs the
 * correct signals to stepper motor.
 *
 * - File:               sm_driver.c
 * - Compiler:           IAR EWAAVR 4.11A
 * - Supported devices:  All devices with a 16 bit timer can be used.
 *                       The example is written for ATmega48
 * - AppNote:            AVR446 - Linear speed control of stepper motor
 *
 * \author               Atmel Corporation: http://www.atmel.com \n
 *                       Support email: avr@atmel.com
 *
 * $Name: RELEASE_1_0 $
 * $Revision: 1.2 $
 * $RCSfile: sm_driver.c,v $
 * $Date: 2006/05/08 12:25:58 $
 *****************************************************************************/

#include <avr/io.h>
#include "global.h"
#include "sm_driver.h"
#include <HardwareSerial.h>

#define STEPPER1_HIGH        PORTD |=  0b00010010;
#define STEPPER1_LOW         PORTD &= ~0b00010010;


//! Table with control signals for stepper motor

//! Position of stepper motor (relative to starting position as zero)
int stepPosition = 0;

/*! \brief Init of io-pins for stepper motor.
 */
void sm_driver_Init_IO(void)
{
  // Init of IO pins
  SM_PORT &= ~((1<<A1) | (1<<A2) | (1<<B1) | (1<<B2)); // Set output pin registers to zero
  SM_DRIVE |= ((1<<A1) | (1<<A2) | (1<<B1) | (1<<B2)); // Set output pin direction registers to output
}

/*! \brief Move the stepper motor one step.
 *
 *  Makes the stepcounter inc/dec one value and outputs this to the
 *  steppermotor.
 *  This function works like a stepper motor controller, a call to the function
 *  is the stepping pulse, and parameter 'inc' is the direction signal.
 *
 *  \param inc  Direction to move.
 *  \return  Stepcounter value.
 */
unsigned char sm_driver_StepCounter(signed char inc)
{
  // Counts 0-1-...-6-7 in halfstep, 0-2-4-6 in fullstep
  static unsigned char counter = 0;
  // Update
  if(inc == CCW){
    stepPosition--;
  }
  else{
    stepPosition++;
  }

  STEPPER1_HIGH
  STEPPER1_LOW
}
