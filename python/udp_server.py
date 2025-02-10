import socket
import json
import select

class UDPServer:
    def __init__(self, ip='192.168.2.209', port=8765, buffer_size=1024):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((ip, port))
        self.sock = self.server_socket
        self.buffer_size = buffer_size
        print(f"UDP server listening on {ip}:{port}")
        self.sock.setblocking(False)

    def receive_data(self):
        last_data = None
        while True:
            try:
                data, addr = self.sock.recvfrom(self.buffer_size)
                last_data = data
            except socket.error:
                break
        if last_data is not None:
            try:
                return json.loads(last_data.decode())
            except json.JSONDecodeError:
                return None
        else:
            return None

if __name__ == "__main__":
    udp_server = UDPServer(
        ip='192.168.2.209',
        port=8765,
        buffer_size=1024
    )

    while True:
        data = udp_server.receive_data()
        if data is not None:
            print(data)
        else:
            print("No data received")