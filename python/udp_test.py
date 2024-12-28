import asyncio
import threading
import queue
from websockets.server import serve

# Create a queue to share data between threads
message_queue = queue.Queue()

async def handle_message(websocket):
    async for message in websocket:
        print(f"Message received: {message}")
        message_queue.put(message)  # Put the message in the queue

async def main():
    async with serve(handle_message, "localhost", 8765):
        await asyncio.get_running_loop().create_future()  # run forever

def start_server():
    asyncio.run(main())

# Start the WebSocket server in a separate thread
server_thread = threading.Thread(target=start_server)
server_thread.start()

# Example of how to get data from the queue in the main thread
while True:
    message = message_queue.get()  # This will block until a message is available
    print(f"Message from queue: {message}")
