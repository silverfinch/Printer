import time
from motor_test import motor_test
from Adafruit_BBIO import GPIO as GPIO

motors = [["P9_11","P8_3","P8_4"],
#["P9_12","P8_5","P8_6"],
#["P9_13","P8_7","P8_8"],
#["P9_14","P8_9","P8_10"],
#["P9_15","P8_11","P8_12"],
#["P9_16","P8_13","P8_14"],
["P9_17","P8_15","P8_16"],
["P9_18","P8_17","P8_18"],
["P9_21","P8_19","P8_20"], #skipped the I2C2 pins on the P9 header since they don't work with Adafruit BBIO
["P9_22","P8_21","P8_22"],
["P9_23","P8_23","P8_24"],
["P9_24","P8_25","P8_26"],
["P9_27","P8_31","P8_32"]]

for i in range(len(motors)):
    motor_test(motors[i][0],motors[i][1],motors[i][2])

enL = "P9_25"
enR = "P9_26"
dirL = "P8_27"
dirR = "P8_29"
stepL = "P8_28"
stepR = "P8_30"
GPIO.setup(enL,GPIO.OUT)
GPIO.setup(enR,GPIO.OUT)
GPIO.setup(dirL,GPIO.OUT)
GPIO.setup(dirR,GPIO.OUT)
GPIO.setup(stepL,GPIO.OUT)
GPIO.setup(stepR,GPIO.OUT)
GPIO.output(enL,GPIO.LOW)
GPIO.output(enR,GPIO.LOW)
GPIO.output(dirL,GPIO.LOW)
GPIO.output(dirR,GPIO.LOW)
for i in range(6400):
    GPIO.output(stepL,GPIO.HIGH)
    GPIO.output(stepR,GPIO.HIGH)
    time.sleep(0.000001)
    GPIO.output(stepL,GPIO.LOW)
    GPIO.output(stepR,GPIO.LOW)
    time.sleep(0.000001)

GPIO.output(dirL,GPIO.HIGH)
GPIO.output(dirR,GPIO.HIGH)
for i in range(6400):
    GPIO.output(stepL,GPIO.HIGH)
    GPIO.output(stepR,GPIO.HIGH)
    time.sleep(0.000001)
    GPIO.output(stepL,GPIO.LOW)
    GPIO.output(stepR,GPIO.LOW)
    time.sleep(0.000001)
GPIO.output(enL,GPIO.HIGH)
GPIO.output(enR,GPIO.HIGH)
