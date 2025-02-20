import os
import signal
import subprocess
import psutil
import asyncio
import threading
import time
import ctypes

file = './run_api.txt'

def adjust_command(line, debug=False, keepOpen=True):
    final_line = line
    if keepOpen:
        final_line = final_line.replace('/C', '/K') 
    if debug:
        final_line = final_line.replace('start', 'start /min')
    else:
        final_line = final_line.replace('start', 'start /B')
    return final_line

class Process:
    def __init__(self, command, script_name, debug=False):
        self.command = command
        self.script_name = script_name
        self.pid = None
        self.update_thread = threading.Thread(target=self.update, daemon=True) # daemon=True allows the thread to be killed when the main thread is killed
        self.update_thread.start()
        self.running = False
        self.debug = debug
    def __dict__(self):
        return {
            "command": self.command,
            "script_name": self.script_name,
            "pid": self.pid,
            "running": self.running,
            "debug": self.debug
        }
    def __str__(self):
        return f"{self.script_name}, pid: {self.pid}, running: {self.running}"
    
    def start(self):
        if self.pid:
            print(f"{self.script_name} is already running with pid {self.pid}")
            return
        command = adjust_command(line = self.command, debug=self.debug)
        print(command)
        print(self.debug)
        subprocess.Popen(command, shell=True)
    
    def getpid(self):
        results_pids = []
        for proc in psutil.process_iter():
            try:
                results = proc.as_dict(attrs=['pid', 'name', 'cmdline'])
                cmdline = results['cmdline']
                if 'python.exe' in results['name']:
                    for arg in cmdline:
                        if self.script_name in arg:
                            # print(f"Found {self.script_name} in {results['cmdline']} with pid {results['pid']}")
                            results_pids.append(results['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        if len(results_pids) > 1:
            print(f"Found more than one pid for {self.script_name}: {results_pids}")
            return results_pids[0]
        elif len(results_pids) == 1:
            return results_pids[0]
        else:
            return None
    def toggle_view(self):
        print(f"Toggle view for {self.pid}")
        self.show = not self.show
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        SW_SHOW = 5
        SW_HIDE = 0

        hWnd = kernel32.OpenProcess(0x400 | 0x10, False, self.pid)
        if hWnd:
            if self.show:
                user32.ShowWindow(hWnd, SW_SHOW)
            else:
                user32.ShowWindow(hWnd, SW_HIDE)
            kernel32.CloseHandle(hWnd)

    @staticmethod
    def kill_process(pid):
        if os.name == 'nt':
            os.system(f'taskkill /F /T /PID {pid}')
        else:
            os.kill(pid, signal.SIGKILL)
    
    def kill(self):
        if self.pid:
            self.kill_process(self.pid)
            print(f"Killed process with pid {self.pid}")
        else:
            print(f"No process with name {self.script_name} found")
    
    def restart(self):
        self.kill()
        #wait for the process to die
        while self.pid:
            print(f"Waiting for {self.script_name} to die")
            time.sleep(0.1)
        #start the process
        print(f"Succesfully killed {self.script_name}, restarting")
        self.start()
        while not self.pid:
            print(f"Waiting for {self.script_name} to start")
            time.sleep(0.1)

    def update(self):
        while True:
            return_value = self.getpid()
            self.pid = return_value
            self.running = self.pid is not None
            time.sleep(1)
    
    def _dict_(self):
        return {
            "command": self.command,
            "script_name": self.script_name,
            "pid": self.pid,
            "running": self.running,
            "debug": self.debug
        }

def start_processes() -> list[Process]:
    global file
    processes : list[Process] = []
    data = []
    with open(file, 'r') as f:
        data = f.readlines()
    for line in data:
        script_name = line.split('python ')[1].split(' ')[0]
        p = Process(line, script_name)
        p.start()
        processes.append(p)
    return processes

if __name__ == '__main__':
    processes = start_processes()
    for p in processes:
        print(p)