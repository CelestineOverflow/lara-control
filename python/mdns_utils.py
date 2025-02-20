import threading
import socket
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, ServiceInfo

def register_mdns_service(service_name: str, port: int) -> bool:
    try:
        zeroconf = Zeroconf()
        service_name = f"{service_name}._http._tcp.local."
        service_info = ServiceInfo(
            "_http._tcp.local.",
            service_name,
            addresses=[socket.inet_aton(socket.gethostbyname(socket.gethostname()))],
            port=port,
            properties={b"path": b"/stream.mjpg"},
        )
        zeroconf.register_service(service_info)
        print(f"Registered mDNS service: {service_name} on port {port}")
        return True
    except Exception as e:
        print(f"Error registering mDNS service: {e}")
        return False

def get_mdns_service(service_name, service_type, timeout=5):
    ip_address = None
    port = None
    """
    Look for the target service once and return its ServiceInfo, or None if not found.
    Parameters:
        service_name (str): The name of the service to look for.
        service_type (str): The type of the service to look for.
        timeout (int): The maximum number of seconds to wait for the service to be found.
    Returns:
        ServiceInfo or None: The discovered service information.
    """
    found_info = None
    event = threading.Event()
    
    class MyListener(ServiceListener):
        def add_service(self, zc, service_type, name):
            nonlocal found_info, ip_address, port
            if name == f"{service_name}.{service_type}":
                info = zc.get_service_info(service_type, name)
                if info and info.addresses:
                    found_info = info
                    ip_address = socket.inet_ntoa(info.addresses[0])
                    port = info.port
                    print(f"Found target service {name} with IP: {ip_address}, port: {info.port}")
                    #kill the listener
                    event.set()
                else:
                    print(f"Found target service {name} but no info is available yet.")
            # else:
                # print(f"Ignoring service: {name}")
        
        def update_service(self, zc, service_type, name):
            if name == service_name:
                print(f"Target service {name} updated")
        
        def remove_service(self, zc, service_type, name):
            if name == service_name:
                print(f"Target service {name} removed")
    
    def start_browser():
        local_zeroconf = Zeroconf()
        listener = MyListener()
        ServiceBrowser(local_zeroconf, service_type, listener)

    thread = threading.Thread(target=start_browser, daemon=True)
    thread.start()
    for _ in range(timeout):
        if event.wait(1):
            break
    return ip_address, port
    

if __name__ == "__main__":
    ip_address, port = get_mdns_service("camera_1", "_http._tcp.local.", timeout=5)
    print(f"Service discovery succeeded. IP: {ip_address}, Port: {port}")