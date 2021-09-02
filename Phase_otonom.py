from pwmtests.main_video import setTargetDepth
import threading
import os
import cv2
import time
from pymavlink import mavutil
import random


master = None
recent_boxes = [[1,2,430,40]]

def send_pwm(x =0, y=0 , z = 500, yaw=0 , buttons=0):
    """Send manual pwm to the axis of a joystick. 
    Relative to the vehicle
    x for right-left motion
    y for forward-backwards motion
    z for up-down motion
    r for the yaw axis
        clockwise is -1000
        counterclockwise is 1000
    buttons is an integer with 
    """
    master.mav.manual_control_send(master.target_system,
                                    x,y,z,yaw,buttons)


class OtonomVehicle():
    def __init__(self):
        self.frameDim = 416
        self.frameMid = 208
        self.kp = 1.0
        self.ki = 0.00002
        self.kd = -0.5
        self.preTotal = 0
        self.lastPositionMid = 0
        
        self.locationRight = True
        self.turn = 1
        
        self.phase_finding_start = threading.Event()
        self.phase_locationtest_start = threading.Event()
        self.phase_alignment_start = threading.Event()
        self.phase_end_start = threading.Event()

        self.phase_finding_start.clear()
        self.phase_locationtest_start.clear()
        self.phase_alignment_start.clear()
        self.phase_end_start.set()

        self.phase_finding_thread = threading.Thread(target=self.phaseOne)
        self.phase_finding_thread.start()

        self.phase_locationtest_thread = threading.Thread(target=self.phaseTwo)
        self.phase_locationtest_thread.start()

        self.phase_alignment_thread = threading.Thread(target=self.phaseThree)
        self.phase_alignment_thread.start()

        self.phase_end_thread = threading.Thread(target=self.phaseFour)
        self.phase_end_thread.start()
    
    @property
    def proportionalYawValue(self):
        return self.kp * (208-recent_boxes[0][0])
    
    @property
    def integralYawValue(self):
        if self.preTotal>50:
            self.preTotal=40
        self.preTotal += self.ki * (208-recent_boxes[0][0])
        return self.preTotal
    
    @property
    def derivativeYawValue(self):
        currentMid = recent_boxes[0][0] 
        Diff = currentMid - self.lastPositionMid
        self.lastPositionMid = currentMid
        return Diff

    def phaseOne(self) -> None:
        """Spin until you find the frame"""
        self.phase_finding_start.wait()  ## IF Phase one is active

        while self.phase_finding_start.is_set():
            if len(recent_boxes[0]) != 0: ##recent_boxes has a value
                send_pwm(yaw=self.proportionalYawValue+self.integralYawValue+self.derivativeYawValue)
                if 178 < recent_boxes[0] < 238: ##Close to center
                    self.phase_finding_start.clear()
                    self.phase_locationtest_start.set()
            else:
                send_pwm(yaw=400)

        self.phaseOne()
    
    def phaseTwo(self) -> None:
        """Determines the turn direction"""
        self.phase_locationtest_start.wait() ## IF Phase two is active
        
        while self.phase_locationtest_start.is_set():
            startTime = time.time()
            startRatio = recent_boxes[0][2]/recent_boxes[0][3]

            while time.time()<startTime+6:
                send_pwm(y=500*self.turn, yaw=-200*self.turn+self.proportionalYawValue) ##c-clockwise
            endRatio = recent_boxes[0][2]/recent_boxes[0][3]
            if endRatio>startRatio:
                self.turn = -1 ## clockwise turn around the frame
            else:
                self.turn = 1 ## counterclockwise turn
            self.phase_locationtest_start.clear()

        self.phaseTwo()
            

    def phaseThree(self)-> None:
        self.phase_alignment_start.wait()  ## IF Phase three is active
        while self.phase_alignment_start.is_set():
            if recent_boxes[0][2]/recent_boxes[0][3]>1.3 and recent_boxes[0][0]<238 and recent_boxes[0][0]>178: ##at most 30 degrees fail
                self.phase_alignment_start.clear()
            else:
                send_pwm(y= 350*self.turn, yaw= -200*self.turn+self.proportionalYawValue)
          

        self.phaseThree()

    def phaseFour(self) -> None:
        self.phase_end_start.wait()   ## IF Phase four is active
        
        while self.phase_end_start.is_set():
            #send_pwm(x=400)
            send_pwm(x=400, yaw=self.proportionalYawValue/3)
           
            recent_boxes[0][0] += (-250+self.proportionalYawValue+self.integralYawValue+self.derivativeYawValue)
            
            time.sleep(1)

        self.phaseFour()

# print(f'Mid X value{recent_boxes[0][0]}')
# print(f'Derivative {self.derivativeYawValue}')
# print(f'Integral {self.integralYawValue}')
# print(f'Proportional {self.proportionalYawValue}')
#addition = 100
# print(f'added {addition}')
Vehicle = OtonomVehicle()
