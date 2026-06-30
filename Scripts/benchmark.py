from multiprocessing import Process
import psutil
import os

def benchmark():
    current_process = psutil.Process()
    current_process.cpu_affinity([0])

    current_cores = current_process.cpu_affinity()
    print(f"Processo {os.getpid()} travado e rodando no Core: {current_cores}")

    for _ in range(999999999999):
        print(_)

if __name__ == "__main__":
    Process(target=benchmark, args=()).start()