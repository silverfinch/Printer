import Adafruit_BBIO.GPIO as GPIO
import time
def motor_test(en,dir,step):
 delay = .000001
 GPIO.setup(en, GPIO.OUT)
 GPIO.setup(dir, GPIO.OUT)
 GPIO.setup(step, GPIO.OUT)
 GPIO.output(en, GPIO.LOW)
 GPIO.output(dir, GPIO.LOW)
 GPIO.output(step, GPIO.LOW)
 for x in range(1,6400):
    GPIO.output(step, GPIO.HIGH)
    time.sleep(delay)
    GPIO.output(step, GPIO.LOW)
    time.sleep(delay)
 GPIO.output(dir, GPIO.HIGH)
 for x in range(1,6400):
    GPIO.output(step, GPIO.HIGH)
    time.sleep(delay)
    GPIO.output(step, GPIO.LOW)
    time.sleep(delay)
 GPIO.cleanup()
