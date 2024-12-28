import aiohttp
import asyncio
import socketio

#pip install python-socketio==4.*

sio = socketio.AsyncClient()

@sio.event
def connect():
    print('connection established')
    
@sio.event
def my_message(data):
    print('message received with ', data)
    sio.emit('my response', {'response': 'my response'})

@sio.event
def disconnect():
    print('disconnected from server')

async def set_speed():
    async with aiohttp.ClientSession() as session:
        async with session.patch(
            "http://192.168.2.13:8081/api/cartesian",
            headers={"Content-Type": "application/json"},
            json={"linearVelocity": 0.01}
        ) as response:
            print(await response.text())
            await sio.emit("linearveltrigger", {"data": True})

async def main():
    await sio.connect('http://192.168.2.13:8081')
    await set_speed()
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(main())