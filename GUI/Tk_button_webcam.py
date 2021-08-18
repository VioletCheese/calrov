import threading
from tkinter import *
from PIL import ImageTk, Image
import cv2
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst
import numpy as np
from time import sleep, time
from pymavlink import mavutil
from math import pi as PI
import threading
import datetime
from random import random

#master = mavutil.mavlink_connection("udpin:192.168.2.1:14550")
#master.wait_heartbeat()
#print("Successful Connection!")


cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

root=Tk()
root.title("CALROV GUI")

#Icon
icontmp = Image.open('/home/violetcheese/Documents/CALROV/GUI/gui_images/calrov_logo.jpg')
icon = ImageTk.PhotoImage(icontmp)
root.tk.call('wm','iconphoto',root._w, icon)
# TITLE TEXT
l = Label(root, text = "CALROV")
l.config(font =("Courier", 14))
l.grid(row=0, column=0, columnspan=4)

#Live Video Display
app = Frame(root, bg="white")
video_label = Label(app)
app.grid(row=1,column=0, columnspan=4)
video_label.grid()
total_frame = 0


fps_label = Label(root, text="Fps: 0")
fps_label.grid(row=6, column=1)




img_scale = 1.3
def video_main():
    global img_scale
    global total_frame
    if video_update:
        ret, frame = cap.read()
        if ret:
            
            """cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) #BGR RGB dönüşümü
            height, width = (int(cv2image.shape[1]*img_scale),int(cv2image.shape[0]*img_scale))

            scaled_img = cv2.resize(cv2image,(height, width))
            """
            detected_image = cv2.cvtColor(yolo_detection(frame),cv2.COLOR_BGR2RGB)
            img = Image.fromarray(detected_image)

            #img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.imgtk = imgtk
            video_label.configure(image=imgtk)
            total_frame+=1
    dtime = time()-start_time
    fps_label.config(text=f"Fps: {total_frame/dtime}")
    video_label.after(1,video_main)
###Attitude Info

roll_label = Label(root, text= 'Roll: Default')
pitch_label = Label(root, text= 'Pitch: Default')
yaw_label = Label(root, text= 'Pitch: Default')
##Attitude Config
roll_label.config(font =("Courier", 14))
pitch_label.config(font =("Courier", 14))
yaw_label.config(font =("Courier", 14))
#Packing Attitude
roll_label.grid(row=2, column=0)
pitch_label.grid(row=2, column=1)
yaw_label.grid(row=2, column=2)



'''
##Message Interval
def request_message_interval(message_id: int, frequency_hz: float):
    """
    Request MAVLink message in a desired frequency,
    documentation for SET_MESSAGE_INTERVAL:
        https://mavlink.io/en/messages/common.html#MAV_CMD_SET_MESSAGE_INTERVAL

    Args:
        message_id (int): MAVLink message ID
        frequency_hz (float): Desired frequency in Hz
    """
    master.mav.command_long_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
        message_id, # MAVLINK mesaj tanimi
        1e6 / frequency_hz, # Istenen frekans
        0, # Hedef, (0=arac)
        0, 0, 0, 0)

# Configure AHRS2 message to be sent at 1Hz
#request_message_interval(mavutil.mavlink.MAVLINK_MSG_ID_AHRS2, 5)

# Configure ATTITUDE message to be sent at 2Hz
request_message_interval(mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE, 100)

'''
def attitude_tk():
    
    '''
    global roll_value
    global pitch_value
    global yaw_value
    '''
    if attitude_update:
        try:
            
            rcvpacket = master.recv_match().to_dict()

            if rcvpacket['mavpackettype']=='ATTITUDE':
                roll_value= int(100* rcvpacket['roll'])
                pitch_value = int(100* rcvpacket['pitch'])
                yaw_value = int(100* rcvpacket['yaw'])

                roll_label.config(text=f'Roll: {roll_value}')
                pitch_label.config(text=f'Pitch: {pitch_value}')
                yaw_label.config(text=f'Yaw: {yaw_value}')
                    #tuple halinde istenen verilerin alınması
        except:
            pass
    
    '''
    roll_label.config(text=str(datetime.datetime.now()))
    pitch_label.config(text='')
    yaw_label.config(text='hehe')
    roll_label.after(1, attitude_tk)
    '''
    
    roll_label.after(1, attitude_tk)

### YOLO and DETECTION
## Loading Yolo
net = cv2.dnn.readNet('/home/violetcheese/Documents/CALROV/GUI/Yolo_files/yolov4-tiny.weights','/home/violetcheese/Documents/CALROV/GUI/Yolo_files/yolov4-tiny.cfg')
detection_classes = []
with open('/home/violetcheese/Documents/CALROV/GUI/Yolo_files/coco.names', 'r') as f:
    detection_classes = [line.strip() for line in f.readlines()]
layer_names = net.getLayerNames()
output_layers = [layer_names[i[0]-1] for i in net.getUnconnectedOutLayers()]

#print(detection_classes)


attitude_update=False
video_update = False

def yolo_detection(raw_image):
    """Take in as input a cv2 image"""
    class_ids = []
    confidences = []
    boxes = []
    height , width, ch = raw_image.shape
    blob = cv2.dnn.blobFromImage(raw_image, 0.00392, (416,416), (0,0,0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.4:
                center_x = int(detection[0]*width)
                center_y = int(detection[1]*height)
                w = int(detection[2]*width)
                h = int(detection[3]*height)
                ##Rectangle Draw
                topleft_x = int(center_x-(w/2))
                topleft_y = int(center_y-(h/2))

                boxes.append([topleft_x,topleft_y,w,h])
                confidences.append(float(confidence))
                class_ids.append(class_id)
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    #DISPLAY DETECTION
    total_detections = len(boxes)
    for i in range(total_detections):
        if i in indexes:
            topleft_x, topleft_y, w,h = boxes[i]
            label = detection_classes[class_ids[i]]
            cv2.rectangle(raw_image, (topleft_x,topleft_y), (topleft_x+w,topleft_y+h), (0,100,255), 1)
            cv2.putText(raw_image, label, (topleft_x, topleft_y),cv2.FONT_HERSHEY_COMPLEX,1,(0,165,255))


    return raw_image

def reset_function():
    pass

def toggle_video():
    global video_update
    if video_update:
        video_update=False
    else:
        video_update=True
def toggle_attitude():
    global attitude_update
    if attitude_update:
        attitude_update=False
    else:
        attitude_update=True

###Threads

reset_button = Button(root, command=threading.Thread(target=reset_function).start, text="reset")
video_button = Button(root, command=threading.Thread(target=video_main).start, text='Video Start')
attitude_button = Button(root, command=threading.Thread(target=attitude_tk).start, text="Attitude Start")
toggle_video_button = Button(root, command=toggle_video, text="Toggle Video")
toggle_attitude_button = Button(root, command=toggle_attitude, text="Toggle Attitude")

#Button Placement
reset_button.grid(row=4, column=0)
video_button.grid(row=4, column=1)
attitude_button.grid(row=4, column=2)
toggle_attitude_button.grid(row=4, column=3)
toggle_video_button.grid(row=4,column=4)

"""videothread = threading.Thread(target=video_main)
tk_main_thread = threading.Thread(target=attitude_tk)
root_thread = threading.Thread(target=root.mainloop)
"""
start_time = time()
if __name__ == '__main__':
    root.mainloop()

    
