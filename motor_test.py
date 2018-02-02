import Adafruit_BBIO.GPIO as GPIO
import time

delay = .000001
GPIO.setup("P8_26", GPIO.OUT)
GPIO.setup("P8_27", GPIO.OUT)
GPIO.setup("P9_14", GPIO.OUT)
GPIO.output("P8_26", GPIO.LOW)
GPIO.output("P8_27", GPIO.LOW)
GPIO.output("P9_14", GPIO.LOW)
for x in range(1,6400):
    GPIO.output("P9_14", GPIO.HIGH)
    time.sleep(delay)
    GPIO.output("P9_14", GPIO.LOW)
    time.sleep(delay)
GPIO.output("P9_14", GPIO.HIGH)
for x in range(1,6400):
    GPIO.output("P9_14", GPIO.HIGH)
    time.sleep(delay)
    GPIO.output("P9_14", GPIO.LOW)
    time.sleep(delay)
GPIO.cleanup()
