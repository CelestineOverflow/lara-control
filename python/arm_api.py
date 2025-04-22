import time
import requests
import random
import time
from packaging import version
from functools import wraps
__version__ = "0.0.22"
# URLs for fetching version and module
version_url = "http://192.168.2.209:1442/api_version"
module_url = "http://192.168.2.209:1442/api_module"
# Fetch the latest version from the API
r_ver = requests.get(version_url) 
if r_ver.status_code != 200:
    print(f"Failed to fetch version info. Status code: {r_ver.status_code}")
else:
    fetched_version = r_ver.json().get("version")
    if version.parse(fetched_version) > version.parse(__version__):
        print(f"Current version: {__version__}, New version available: {fetched_version}")
        print("Downloading the latest version...")
        # Download the latest version
        r_module = requests.get(module_url)
        if r_module.status_code == 200:
            with open("arm_api.py", "wb") as f:
                f.write(r_module.content)
            print("Successfully downloaded the latest version, please restart the script.")
            raise Exception("Restart the script to apply the new version.")
        else:
            print(f"Failed to download the module. Status code: {r_module.status_code}")

def notify_user(type: str, message: str):
    # dont look this up, it's a secret
    info_gifs_urls = ['https://www.icegif.com/wp-content/uploads/2022/01/icegif-1787.gif', 'https://i.pinimg.com/originals/99/86/cb/9986cb5fff621512eb94a52e93f05a35.gif', 'https://c.tenor.com/wtUhaT9-NEEAAAAd/tenor.gif', 'https://media.tenor.com/QgIYHDiMR4EAAAAM/rocket-shi-rocket-bomb.gif']
    success_gif_urls = ['https://i.pinimg.com/originals/0b/51/1b/0b511b93d6fd37c448fc761e3edf2206.gif','https://media.tenor.com/LiqhUEDmWcAAAAAM/cute.gif', 'https://notsopersonalblog.weebly.com/uploads/1/9/1/0/19105387/9965518_orig.gif', 'https://media.tenor.com/GuzFcXzoL2MAAAAM/moonlanding.gif']
    error_gif_urls = ['https://media.tenor.com/YTPLqiB6gLsAAAAM/sowwy-sorry.gif', 'https://media.tenor.com/IsmWQg-Ge-UAAAAM/explo-xd.gif', 'https://media.tenor.com/2-MpRS4tcE8AAAAM/run-explosions.gif', 'https://media.tenor.com/asSa0XkcXXwAAAAM/rocket-failure-explode.gif']
    
    # Select the appropriate GIF based on the type
    if type.lower() == "success":
        gif_url = random.choice(success_gif_urls)
    elif type.lower() == "error":
        gif_url = random.choice(error_gif_urls)
    else:  # Use info gifs as default
        gif_url = random.choice(info_gifs_urls)
    
    url = "https://prod-219.westeurope.logic.azure.com:443/workflows/bf7984aa748242e980a0d4d1475db9e4/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=kqRPY8zkisJzhYcr6vkYrY07QoPVZX6CFIeWTZWGLu8"
    myobj = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.0",
                        "msteams": {
                            "width": "Full"
                        },
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": type,
                                "weight": "bolder",
                                "size": "medium",
                                "wrap": "true"
                            },
                            {
                                "type": "TextBlock",
                                "text": message,
                                "wrap": "true"
                            },
                            {
                                "type": "Image",
                                "url": gif_url,
                                "horizontalAlignment": "center"
                            }
                        ]
                    }
                }
            ]
        }
    try:
        x = requests.post(url, json=myobj)
        print(x.text)
    except Exception as e:
        print(f"Failed to send notification: {e}")
        return

def restart_script(script_name: str):
    url = f'http://192.168.2.209:8765/restart_process?script_name={script_name}'
    response = requests.get(url)
    if response.status_code != 200:
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def to_socket():
    url = f'http://192.168.2.209:1442/to_socket'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def to_tray():
    url = f'http://192.168.2.209:1442/to_tray'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def set_autonomous_control(state: bool):
    url = f'http://192.168.2.209:1442/setAutonomousControl?autonomous_control={state}'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def move_to_cell(row: int, col: int):
    url = f'http://192.168.2.209:1442/moveToCell?row={row}&col={col}'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def move_to_cell_retract(row: int, col: int):
    url = f'http://192.168.2.209:1442/moveToCellRetract?row={row}&col={col}'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def move_until_pressure(pressure: int, wiggle_room: int):
    url = f'http://192.168.2.209:1442/moveUntilPressure?pressure={pressure}&wiggle_room={wiggle_room}'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def toggle_pump(state: bool):
    url = f'http://192.168.2.209:1442/togglePump?boolean={state}'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def move_to_socket():
    url = f'http://192.168.2.209:1442/moveToSocket'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def move_to_socket_smart():
    url = f'http://192.168.2.209:1442/moveToSocketSmart'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def move_to_socket_retract():
    url = f'http://192.168.2.209:1442/moveToSocketRetract'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def get_current_pump_pressure() -> int:
    url = f'http://192.168.2.209:1442/current_pump_pressure'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['pressure']
    else:
        notify_user("Error", response.text)
        raise Exception(response.text)

def retract(distance = -0.3):
    url = f'http://192.168.2.209:1442/retract?distance={distance}'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def set_brightness(brightness: int):
    url = f'http://192.168.2.209:1442/setBrightness?newBrightness={brightness}'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def set_heater(heat: int):
    url = f'http://192.168.2.209:1442/setHeater?newHeat={heat}'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)

def wait_for_temperature(heat: int):
    url = f'http://192.168.2.209:1442/wait_for_temperature?newHeat={heat}'
    response = requests.post(url)
    if response.status_code != 200 or "error" in response.text.lower():
        notify_user("Error", response.text)
        raise Exception(response.text)
    print(response.text)


# wait_for_temperature



class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tested = False
        self.passed = False

    @staticmethod
    def generate_cells(start_cell, end_cell) -> list:
        cells = []
        for i in range(start_cell[0], end_cell[0]):
            for j in range(start_cell[1], end_cell[1]):
                cells.append(Cell(i, j))
        return cells


execution_counter = 0

def labhandler_sequence(func):
    @wraps(func)
    def wrapper(cell, *args, **kwargs):
        global execution_counter
        try:
            set_heater(0)
            execution_counter += 1
            print(f'Testing cell x: {cell.x} y: {cell.y}')
            # Pre-test steps
            toggle_pump(False)
            move_to_cell(cell.x, cell.y)
            move_until_pressure(1000, 50)
            for j in range(3):
                toggle_pump(True)
                time.sleep(1)
                retract(-0.3)
                pump_pressure = get_current_pump_pressure()
                print(f'Pump pressure: {pump_pressure}')
                if pump_pressure < 150:
                    break
                if j == 2:
                    print('Failed to reach pressure, cancelling test')
                    toggle_pump(False)
                    raise Exception('Failed to reach pressure')
                toggle_pump(False)
                move_to_cell_retract(cell.x, cell.y)
                move_until_pressure(1000, 50)
            to_socket()
            move_to_socket_retract()
            toggle_pump(False)
            time.sleep(5)
            move_until_pressure(5000, 100)
            time.sleep(5)
            # ------------------- User Test -------------------
            try:
                func(*args, **kwargs)
                cell.tested = True
                cell.passed = True
            except Exception as e:	
                print(f'Exception in user test: {e}')
                notify_user("Error", f'Failed to test cell x: {cell.x} y: {cell.y}')
                cell.tested = True
                cell.passed = False
            # ------------------- User Test -------------------
            time.sleep(3)
            for j in range(3):
                toggle_pump(True)
                time.sleep(5)
                retract(-0.3)
                pump_pressure = get_current_pump_pressure()
                print(f'Pump pressure: {pump_pressure}')
                if pump_pressure < 150:
                    break  
                toggle_pump(False)
                move_to_socket_retract()
                move_until_pressure(1000, 300)
            to_tray()
            move_to_cell_retract(cell.x, cell.y)
            MAX_RETRIES = 20
            for j in range(MAX_RETRIES):
                toggle_pump(False)
                time.sleep((j+1)*1) # from 1 to 20 seconds
                toggle_pump(True)
                time.sleep(2)
                pump_pressure = get_current_pump_pressure()
                print(f'Pump pressure: {pump_pressure}')
                if pump_pressure > 150:
                    break
                if j == MAX_RETRIES - 1:
                    notify_user("Error", f'sample stuck in plunger')
                    raise Exception('sample stuck in plunger')
            toggle_pump(False)
            notify_user("Success", f'Tested cell x: {cell.x} y: {cell.y}')
            if execution_counter >= 5:
                print('Restarting camera.py, to avoid memory leak')
                restart_script("camera.py")
                time.sleep(30)
                execution_counter = 0
        except Exception as e:
            print(f'Exception in test: {e}')
            notify_user("Error", f'Failed to test cell x: {cell.x} y: {cell.y}')
            raise e
    return wrapper