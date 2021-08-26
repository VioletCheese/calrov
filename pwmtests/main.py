### IMPORTS
##GUI
from posix import posix_spawn
from tkinter import *
from PIL import ImageTk, Image
import cv2
##SYSTEM IMPORT
import threading
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst
from time import sleep, time
from pymavlink import mavutil
from math import pi as PI
import numpy as np
import threading
import datetime
import os.path




### TINTER INITIALIZING
root=Tk()
root.title("CALROV GUI")

##Icon
icontmp = Image.open(os.path.abspath('./GUI/gui_images/calrov_logo.jpg'))
icon = ImageTk.PhotoImage(icontmp)
root.tk.call('wm','iconphoto',root._w, icon)

## TITLE TEXT
Title_label = Label(root, text = "CALROV")
Title_label.config(font =("Courier", 14))
Title_label.grid(row=0, column=0, columnspan=4)

##Live Video Display Box
video_app = Frame(root, bg="white")
video_app.grid(row=1,column=0, columnspan=4)


video_label_yolo = Label(video_app)
video_label_yolo.grid(row=0)
video_label_opencv = Label(video_app)
video_label_opencv.grid(row=1)




fps_label = Label(root, text="Fps: 0")
fps_label.grid(row=6, column=1)


###  GLOBAL VARIABLES AND OBJECTS
video = Video(port=4777)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

recent_boxes = []

video_on = True

### FUNCTION AND CLASS DEFINITIONS
class Video():

    """BlueRov video capture class constructor

    Attributes:
        port (int): Video UDP port
        video_codec (string): Source h264 parser
        video_decode (string): Transform YUV (12bits) to BGR (24bits)
        video_pipe (object): GStreamer top-level pipeline
        video_sink (object): Gstreamer sink element
        video_sink_conf (string): Sink configuration
        video_source (string): Udp source ip and port
    """

    def __init__(self, port=5600):
        """Summary

        Args:
            port (int, optional): UDP port
        """

        Gst.init(None)

        self.port = port
        self._frame = None

        # [Software component diagram](https://www.ardusub.com/software/components.html)
        # UDP video stream (:5600)
        self.video_source = 'udpsrc port={}'.format(self.port)
        # [Rasp raw image](http://picamera.readthedocs.io/en/release-0.7/recipes2.html#raw-image-capture-yuv-format)
        # Cam -> CSI-2 -> H264 Raw (YUV 4-4-4 (12bits) I420)
        self.video_codec = '! application/x-rtp, payload=96 ! rtph264depay ! h264parse ! avdec_h264'
        # Python don't have nibble, convert YUV nibbles (4-4-4) to OpenCV standard BGR bytes (8-8-8)
        self.video_decode = \
            '! decodebin ! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert'
        # Create a sink to get data
        self.video_sink_conf = \
            '! appsink emit-signals=true sync=false max-buffers=2 drop=true'

        self.video_pipe = None
        self.video_sink = None

        self.run()

    def start_gst(self, config=None):
        """ Start gstreamer pipeline and sink
        Pipeline description list e.g:
            [
                'videotestsrc ! decodebin', \
                '! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
                '! appsink'
            ]

        Args:
            config (list, optional): Gstreamer pileline description list
        """

        if not config:
            config = \
                [
                    'videotestsrc ! decodebin',
                    '! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
                    '! appsink'
                ]

        command = ' '.join(config)
        self.video_pipe = Gst.parse_launch(command)
        self.video_pipe.set_state(Gst.State.PLAYING)
        self.video_sink = self.video_pipe.get_by_name('appsink0')

    @staticmethod
    def gst_to_opencv(sample):
        """Transform byte array into np array

        Args:
            sample (TYPE): Description

        Returns:
            TYPE: Description
        """
        buf = sample.get_buffer()
        caps = sample.get_caps()
        array = np.ndarray(
            (
                caps.get_structure(0).get_value('height'),
                caps.get_structure(0).get_value('width'),
                3
            ),
            buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)
        return array

    def frame(self):
        """ Get Frame

        Returns:
            iterable: bool and image frame, cap.read() output
        """
        return self._frame

    def frame_available(self):
        """Check if frame is available

        Returns:
            bool: true if frame is available
        """
        return type(self._frame) != type(None)

    def run(self):
        """ Get frame to update _frame
        """

        self.start_gst(
            [
                self.video_source,
                self.video_codec,
                self.video_decode,
                self.video_sink_conf
            ])

        self.video_sink.connect('new-sample', self.callback)

    def callback(self, sink):
        sample = sink.emit('pull-sample')
        new_frame = self.gst_to_opencv(sample)
        self._frame = new_frame

        return Gst.FlowReturn.OK

def video_main():
    global recent_boxes
    if video_on and video.frame_available():
        
        frame = video.frame()
    
        """cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) #BGR RGB dönüşümü
        height, width = (int(cv2image.shape[1]*img_scale),int(cv2image.shape[0]*img_scale))

        scaled_img = cv2.resize(cv2image,(height, width))
        """
        # detected_image, recent_boxes = yolo_detection(frame)
        # detected_image = cv2.cvtColor(detected_image,cv2.COLOR_BGR2RGB)
        # img = Image.fromarray(detected_image)
        
        #img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)
        pwm_decide_once(detected_image, recent_boxes)
    video_label.after(1,video_main)

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
    master.mav.manual_control_send(master.target_system, x,y,z,yaw,buttons)

###THREADS
video_button = Button(root, command=threading.Thread(target=video_main).start, text='Video Start')




video_button.grid()





if __name__ == "__main__":
    root.mainloop()