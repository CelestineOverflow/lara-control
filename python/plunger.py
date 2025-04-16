import time
import serial
import logging
import multiprocessing
import json
import requests
import traceback
from multiprocessing.managers import BaseManager
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
max_pressure = 12000.0
class LatestValueHolder:
   """Class to safely store the latest value across processes."""
   def __init__(self):
       self.lock = multiprocessing.Lock()
       self.value = None
       self._has_new_data = multiprocessing.Value('b', False)
   def set(self, value):
       """Set a new value."""
       with self.lock:
           self.value = value
           self._has_new_data.value = True
   def get(self):
       """Get the latest value and mark as read."""
       with self.lock:
           if not self._has_new_data.value:
               return None
           self._has_new_data.value = False
           return self.value
   def peek(self):
       """Get the latest value without marking as read."""
       with self.lock:
           return self.value
   def has_new_data(self):
       """Check if there is new data available."""
       return self._has_new_data.value
# Register the custom class with multiprocessing manager
BaseManager.register('LatestValueHolder', LatestValueHolder)
def serial_worker(port, baudrate, input_queue, value_holder, running_flag):
   previous_pressure = 0.0
   ser = None
   def connect():
       nonlocal ser
       while running_flag.value:
           try:
               ser = serial.Serial(port, baudrate, timeout=0.1)
               if ser.isOpen():
                   logger.info(f"Connected to {port}")
                   return True
               time.sleep(1)
           except serial.SerialException as e:
               logger.error(f"Failed to connect to {port}: {e}")
               time.sleep(2)  # Wait before retrying
           except Exception as e:
               logger.error(f"Error connecting to {port}: {e}")
               time.sleep(2)  # Wait before retrying
       return False
   if not connect():
       logger.error(f"Could not connect to {port}. Exiting worker.")
       return
   buffer = ""
   while running_flag.value:
       try:
           # Read data with timeout
           data = ser.read(1024).decode("utf-8", errors='ignore')
           if data:
               buffer += data
               while "\n" in buffer:
                   line, buffer = buffer.split("\n", 1)
                   line = line.strip()
                   if line:
                       try:
                           parsed_json = json.loads(line)
                           # Handle pressure monitoring
                           if 'force' in parsed_json and parsed_json['force']:
                               value = float(parsed_json['force'])
                               # Emergency stop if pressure is too high for consecutive readings
                               if value > max_pressure and previous_pressure > max_pressure:
                                   logger.error(f"Pressure value too high: {value}")
                                   try:
                                       response = requests.request("POST", "http://192.168.2.209:1442/EmergencyStop", timeout=2)
                                       if response.status_code == 200:
                                           logger.info("Emergency stop request sent successfully")
                                       else:
                                           logger.error(f"Failed to send emergency stop request. Status code: {response.status_code}")
                                   except requests.RequestException as e:
                                       logger.error(f"Network error when sending emergency stop: {e}")
                               previous_pressure = value
                           # Update the latest value (no queue full issues)
                           value_holder.set(parsed_json)
                       except json.JSONDecodeError as e:
                           logger.error(f"JSON decode error: {e} - Line: {line}")
                       except Exception as e:
                           logger.error(f"Error processing data: {e}")
                           logger.error(f"Traceback: {traceback.format_exc()}")
           # Process commands from the input queue
           try:
               while True:  # Process all available commands
                   command = input_queue.get_nowait()
                   if ser and ser.isOpen():
                       ser.write((command + '\n').encode('utf-8'))
                       logger.info(f"Sent: {command}")
                   else:
                       logger.error(f"Cannot send command, serial port not open: {command}")
           except multiprocessing.queues.Empty:
               pass  # No more commands in queue
           # Small sleep to prevent CPU thrashing
           time.sleep(0.001)
       except serial.SerialException as e:
           logger.error(f"Serial error: {e}")
           # Try to reconnect
           ser.close()
           if not connect():
               break
       except UnicodeDecodeError:
           pass  # Skip non-UTF8 data
       except Exception as e:
           logger.error(f"Unexpected error in serial worker: {e}")
           logger.error(traceback.format_exc())
           time.sleep(0.5)  # Prevent tight error loops
   # Cleanup
   if ser and ser.isOpen():
       ser.close()
   logger.info(f"Serial worker for {port} stopped")
class Plunger:
   def __init__(self, port, baudrate, name="Plunger"):
       self.port = port
       self.baudrate = baudrate
       self.name = name
       # Create a multiprocessing manager
       self.manager = BaseManager()
       self.manager.start()
       # Create the value holder for latest data
       self.value_holder = self.manager.LatestValueHolder()
       # Command queue (no size limit needed)
       self.input_queue = multiprocessing.Queue()
       # Running flag
       self.running = multiprocessing.Value('b', True)
       # Create process
       self.process = multiprocessing.Process(
           target=serial_worker,
           args=(self.port, self.baudrate, self.input_queue, self.value_holder, self.running)
       )
   def start(self):
       """Start the serial worker process."""
       self.process.start()
       logger.info(f"Started {self.name} on {self.port}")
   def write(self, command):
       """Send a command to the device."""
       self.input_queue.put(command)
   def read(self):
       """Get the latest value if available (returns None if no new data)."""
       return self.value_holder.get()
   def peek(self):
       """Look at the current value without marking it as read."""
       return self.value_holder.peek()
   def has_new_data(self):
       """Check if new data is available."""
       return self.value_holder.has_new_data()
   def stop(self):
       """Stop the serial worker process."""
       logger.info(f"Stopping {self.name}...")
       self.running.value = False
       # Wait for process to terminate with timeout
       self.process.join(timeout=5)
       # Force terminate if it didn't exit cleanly
       if self.process.is_alive():
           logger.warning(f"Process did not terminate gracefully, forcing termination.")
           self.process.terminate()
           self.process.join()
       # Shutdown the manager
       self.manager.shutdown()
       logger.info(f"{self.name} stopped")
if __name__ == "__main__":
   # Example usage
   serial_handler = Plunger("COM13", 115200)
   serial_handler.start()
   try:
       while True:
           # Check for new data without blocking
           if serial_handler.has_new_data():
               data = serial_handler.read()
               logger.info(f"Received: {data}")
           # You can also peek at the latest value without marking it as read
           # latest = serial_handler.peek()
           # Add a small sleep to prevent CPU thrashing
           time.sleep(0.05)
   except KeyboardInterrupt:
       logger.info("Shutting down...")
   finally:
       serial_handler.stop()
       logger.info("Program terminated")