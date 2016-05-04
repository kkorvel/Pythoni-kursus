import cv2
import numpy as np
import signal
import sys
from flask import Flask, render_template, Response
from collections import deque
from datetime import datetime
from time import time, sleep
from threading import Thread
from PyMata.pymata import PyMata
 
class Motors(Thread):
    MOTOR_1_PWM = 2
    MOTOR_1_A   = 3
    MOTOR_1_B   = 4
    MOTOR_2_PWM = 5
    MOTOR_2_A   = 6
    MOTOR_2_B   = 7
    MOTOR_3_PWM = 8
    MOTOR_3_A   = 9
    MOTOR_3_B   = 10
 
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.running = True
        self.board = PyMata()
        def signal_handler(sig, frame):
            self.running = False
            self.board.reset()
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)
        self.board.set_pin_mode(self.MOTOR_1_PWM, self.board.PWM,    self.board.DIGITAL)
        self.board.set_pin_mode(self.MOTOR_1_A,   self.board.OUTPUT, self.board.DIGITAL)
        self.board.set_pin_mode(self.MOTOR_1_B,   self.board.OUTPUT, self.board.DIGITAL)
        self.board.set_pin_mode(self.MOTOR_2_PWM, self.board.PWM,    self.board.DIGITAL)
        self.board.set_pin_mode(self.MOTOR_2_A,   self.board.OUTPUT, self.board.DIGITAL)
        self.board.set_pin_mode(self.MOTOR_2_B,   self.board.OUTPUT, self.board.DIGITAL)
        self.board.set_pin_mode(self.MOTOR_3_PWM, self.board.PWM,    self.board.DIGITAL)
        self.board.set_pin_mode(self.MOTOR_3_A,   self.board.OUTPUT, self.board.DIGITAL)
        self.board.set_pin_mode(self.MOTOR_3_B,   self.board.OUTPUT, self.board.DIGITAL)
        self.dx, self.dy = 0, 0
 
    def run(self):
        while self.running:
            # Reset all direction pins to avoid damaging H-bridges
            self.board.digital_write(self.MOTOR_1_B, 0)
            self.board.digital_write(self.MOTOR_1_A, 0)
            self.board.digital_write(self.MOTOR_2_B, 0)
            self.board.digital_write(self.MOTOR_2_A, 0)
            self.board.digital_write(self.MOTOR_3_B, 0)
            self.board.digital_write(self.MOTOR_3_A, 0)
 
            dist = abs(self.dx)
            if dist > 2:
                if self.dx > 0:
                    print("Turning left")
                    self.board.digital_write(self.MOTOR_1_B, 1)
                    self.board.digital_write(self.MOTOR_2_B, 1)
                    self.board.digital_write(self.MOTOR_3_B, 1)
                else:
                    print("Turning right")
                    self.board.digital_write(self.MOTOR_1_A, 1)
                    self.board.digital_write(self.MOTOR_2_A, 1)
                    self.board.digital_write(self.MOTOR_3_A, 1)
                self.board.analog_write(self.MOTOR_1_PWM, int(dist ** 0.5 + 25))
                self.board.analog_write(self.MOTOR_2_PWM, int(dist ** 0.5 + 25))
                self.board.analog_write(self.MOTOR_3_PWM, int(dist ** 0.5 + 25))
            elif self.dy > 30:
                print("Going forward")
                self.board.digital_write(self.MOTOR_1_B, 1)
                self.board.digital_write(self.MOTOR_3_A, 1)
                self.board.analog_write(self.MOTOR_1_PWM, int(self.dy ** 0.5 )+30)
                self.board.analog_write(self.MOTOR_2_PWM, 0)
                self.board.analog_write(self.MOTOR_3_PWM, int(self.dy ** 0.5 )+30)
            sleep(0.03)
 
class FrameGrabber(Thread):
    BALL_LOWER = ( 5, 140, 140)
    BALL_UPPER = (30, 255, 255)
 
    def __init__(self, width=640, height=480):
        Thread.__init__(self)
        self.daemon = True
        self.video = cv2.VideoCapture(0)
        self.video.set(3, width)
        self.video.set(4, height)
        self.timestamp = time()
        self.frames = 0
        self.fps = 50
        self.current_frame = None
 
    def run(self):
        while True:
            self.frames += 1
            timestamp_begin = time()
            if self.frames > 10:
                self.fps = self.frames / (timestamp_begin - self.timestamp)
                self.frames = 0
                self.timestamp = timestamp_begin
            success, frame = self.video.read()
            frame = cv2.flip(frame, 1)
            original = frame
            blurred = cv2.blur(frame, (4,4))
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, self.BALL_LOWER, self.BALL_UPPER)
            mask = cv2.dilate(mask, None, iterations=2)
            cutout = cv2.bitwise_and(frame,frame, mask= mask)
            cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
            found_any = False
            if len(cnts) > 0:
                c = max(cnts, key=cv2.contourArea)
                (x, y), radius = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                if radius > 5:
                    cv2.circle(frame, (int(x), int(y)), int(radius),
                        (0, 255, 255), 2)
                    cv2.circle(frame, center, 5, (0, 0, 255), -1)
                    radius = 1/radius
                    radius = round(radius*100*11.35, 2)
                    cv2.putText(original,str(radius),(int(x),int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.7,(255,255,255),1)
                    cv2.putText(original,str(radius),(int(x+3),int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.59,(0,0,0),1)
                    delta = int((x-320)/5.0)
                    motors.dx, motors.dy = delta, 240-y
                    found_any = True
            if not found_any:
                motors.dx, motors.dy = 0, 0
            cv2.putText(frame,"%.01f fps" % self.fps, (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.3,(255,255,255),1)
            self.current_frame = np.hstack([original, cutout])

 
motors = Motors()
grabber = FrameGrabber()
motors.start()
grabber.start()
 
app = Flask(__name__)
 
@app.route('/')
def index():
    def generator():
        while True:
            if grabber.current_frame != None:
                ret, jpeg = cv2.imencode('.jpg', grabber.current_frame, (cv2.IMWRITE_JPEG_QUALITY, 20))
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tostring() + b'\r\n\r\n'
            sleep(0.1) # Approx 10fps for web browser
    return Response(generator(), mimetype='multipart/x-mixed-replace; boundary=frame')
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True,use_reloader=False,threaded=True)