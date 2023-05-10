import socket

START_PORT = 8001
END_PORT = 9999

def find_available_port_in_range(start_port, end_port):
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return port
            except OSError:
                continue
    raise RuntimeError("No available ports in the given range")

def find_dashboard_port():
    return find_available_port_in_range(START_PORT, END_PORT)