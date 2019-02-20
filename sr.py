import time
from serial import Serial


ser = Serial('/dev/ttyUSB0', 115200)


while 1:
    serial_line = ser.readline()

    print(serial_line) # If using Python 2.x use: print serial_line
    # Do some other work on the data

    # time.sleep(300) # sleep 5 minutes

    # Loop restarts once the sleep is finished

ser.close()
