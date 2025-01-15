import math
import socket
import threading
import time

from Constants import (
    BROADCAST_PORT_TO, BROADCAST_PORT_FROM, BUFFER_SIZE, BROADCAST_IP, UDP_SERVER_PORT, TCP_SERVER_PORT,
    PACKET_SIZE
)
from ServerClient.Message import build_offer_message, parsed_message_request, build_payload_message_udp

SERVER_IP = socket.gethostbyname(socket.gethostname())
BROADCAST_ADDR_TO = (BROADCAST_IP, BROADCAST_PORT_TO)  # This address is to sent to all localhost
BROADCAST_ADDR_FROM = (SERVER_IP, BROADCAST_PORT_FROM)  # This is the address that the socket is on the server side

# ANSI Colors for printing
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"  # For UDP
BLUE = "\033[94m"  # For TCP


def main():
    print(f"{CYAN}Starting server...{RESET}")
    broadcast_thread = threading.Thread(
        target=broadcasting,
        kwargs=dict(udp_port=UDP_SERVER_PORT, tcp_port=TCP_SERVER_PORT)
    )

    udp_thread = threading.Thread(
        target=run_udp_server,
        args=(UDP_SERVER_PORT,)
    )

    tcp_thread = threading.Thread(
        target=run_tcp_server,
        args=(TCP_SERVER_PORT,)
    )

    tcp_thread.start()
    udp_thread.start()
    broadcast_thread.start()

    tcp_thread.join()
    udp_thread.join()
    broadcast_thread.join()


def broadcasting(udp_port, tcp_port) -> None:
    message = build_offer_message(udp_port, tcp_port)
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            sock.sendto(message, BROADCAST_ADDR_TO)
            time.sleep(1)
            print(f"{GREEN}[BROADCAST] Message sent to {BROADCAST_ADDR_TO}{RESET}")
        except Exception as e:
            print(f"{RED}[BROADCAST ERROR] {e}{RESET}")


def run_tcp_server(tcp_port) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", tcp_port))
    print(f"{BLUE}[TCP SERVER] Listening on {SERVER_IP}:{tcp_port}{RESET}")
    sock.listen(5)
    while True:
        client_sock, client_addr = sock.accept()
        print(f"{BLUE}[TCP SERVER] Connection established with {client_addr}{RESET}")
        threading.Thread(
            target=send_payload_tcp,
            args=(client_sock,)
        ).start()


def send_payload_tcp(client_sock):
    try:
        file_size = client_sock.recv(64).strip()
        print(f"{YELLOW}[TCP SERVER] Received file size request: {file_size.decode()}{RESET}")

        if not file_size:
            print(f"{RED}[TCP SERVER] Empty file size received. Closing connection.{RESET}")
            client_sock.close()
            return

        file_size = int(file_size)
        payload = b"a" * file_size
        client_sock.sendall(payload)

        print(f"{BLUE}[TCP SERVER] Sent payload of size: {len(payload)} bytes{RESET}")
    except Exception as e:
        print(f"{RED}[TCP SERVER ERROR] {e}{RESET}")
    finally:
        client_sock.close()
        print(f"{BLUE}[TCP SERVER] Connection closed{RESET}")


def run_udp_server(udp_port) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", udp_port))
    print(f"{MAGENTA}[UDP SERVER] Listening on port {udp_port}{RESET}")
    while True:
        raw_data, client_addr = sock.recvfrom(BUFFER_SIZE)
        print(f"{MAGENTA}[UDP SERVER] Received data from {client_addr}{RESET}")
        threading.Thread(
            target=send_payload_udp,
            args=(client_addr, raw_data)
        ).start()


def send_payload_udp(client_addr, data) -> None:
    try:
        file_size = parsed_message_request(data)
        print(f"{YELLOW}[UDP SERVER] Parsed file size: {file_size} bytes{RESET}")

        packets_num = math.ceil(file_size / PACKET_SIZE)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        start_time = time.time()
        for seq in range(packets_num):
            start_index = seq * PACKET_SIZE
            remaining = file_size - start_index
            next_packet_size = min(remaining, PACKET_SIZE)
            file = b"a" * next_packet_size

            # Building the message by format
            payload = build_payload_message_udp(packets_num, seq, file)
            sock.sendto(payload, client_addr)
            print(f"{MAGENTA}[UDP SERVER] Sent packet {seq + 1}/{packets_num}, size: {len(payload)} bytes{RESET}")

        end_time = time.time()
        duration = end_time - start_time

    except Exception as e:
        print(f"{RED}[UDP SERVER ERROR] {e}{RESET}")


if __name__ == "__main__":
    main()
