import time
import serial
from queue import Queue
import logging
import multiprocessing
import json
import requests
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

max_pressure = 15000.0
previous_pressure = 0.0 

def serial_worker(port, baudrate, input_queue, output_queue, running_flag):
    global previous_pressure
    ser = None

    def connect():
        nonlocal ser
        while running_flag.value:
            try:
                ser = serial.Serial(port, baudrate, timeout=0)
                if ser.isOpen():
                    logger.info(f"Connected to {port}")
                    return
            except serial.SerialException:
                logger.error(f"Failed to connect to {port}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(1)

    connect()
    buffer = ""
    
    while running_flag.value:
        try:
            data = ser.read(1024).decode("utf-8", errors='ignore')  # Read up to 1024 bytes
            buffer += data

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line:
                    try:
                        parsed_json = json.loads(line)
                        # print(parsed_json)
                        if parsed_json['force']:
                            value = parsed_json['force']
                            value = float(value)
                            if value > max_pressure and previous_pressure > max_pressure:
                                logger.error(f"Pressure value too high: {value}")
                                response = requests.request("POST", "http://localhost:1442/EmergencyStop")
                                if response.status_code == 200:
                                    logger.info("Emergency stop request sent successfully")
                                else:
                                    logger.error("Failed to send emergency stop request")
                            previous_pressure = value
                        output_queue.put_nowait(parsed_json)
                    except:
                        pass

            while not input_queue.empty() and running_flag.value:
                command = input_queue.get()
                ser.write((command + '\n').encode('utf-8'))
                logger.info(f"Sent: {command}")
        except serial.SerialException:
            connect()
        except UnicodeDecodeError:
            pass

    ser.close()

class Plunger:
    def __init__(self, port, baudrate, name="Plunger"):
        self.port = port
        self.baudrate = baudrate
        self.name = name
        self.input = multiprocessing.Queue()
        self.output = multiprocessing.Queue(maxsize=1)  # Buffer to store only the latest value
        self.running = multiprocessing.Value('b', True)
        self.process = multiprocessing.Process(target=serial_worker, args=(self.port, self.baudrate, self.input, self.output, self.running))

    def start(self):
        self.process.start()

    def write(self, command):
        self.input.put(command)

    def stop(self):
        self.running.value = False
        self.process.join()

if __name__ == "__main__":
    serial_handler = Plunger("COM13", 115200)
    serial_handler.start()

    # Example usage:
    try:
        while True:
            if not serial_handler.output.empty():
                line = serial_handler.output.get()
                logger.info(f"Received:​ {line}")
    except KeyboardInterrupt:
        serial_handler.stop()
        logger.info("Stopped")