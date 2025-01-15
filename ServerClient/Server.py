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
BROADCAST_ADDR_TO = (BROADCAST_IP, BROADCAST_PORT_TO) # This address is to sent to all localhost
BROADCAST_ADDR_FROM = (SERVER_IP, BROADCAST_PORT_FROM) # This is the address that the socket is on the server side

# Constant


def main():
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

    print(f'Server started, listening on IP address {SERVER_IP}')
    tcp_thread.start()
    udp_thread.start()
    broadcast_thread.start()

    tcp_thread.join()
    udp_thread.join()
    broadcast_thread.join()

def broadcasting(udp_port, tcp_port) -> None:
    massage = build_offer_message(udp_port, tcp_port)
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            sock.sendto(massage, BROADCAST_ADDR_TO)
            time.sleep(1)
            print("Broadcasting message") #NEED TO CHANGEEEEE
        except Exception as e:
            print(e) #NEED TO CHANGEEEE



def run_tcp_server(tcp_port) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((SERVER_IP, tcp_port))
    sock.listen(5)
    while True:
        client_sock, client_addr = sock.accept()

        payload_thread = threading.Thread(
            target=sent_payload_tcp,
            args=(client_sock,)
        ).start()


def sent_payload_tcp(client_sock):
    try:
        print("Sending message")
        message = client_sock.recv(BUFFER_SIZE)
        file_size = parsed_message_request(message)

        print(f"DBG: Received filesize of {len(file_size)} bytes")

        payload = b"a" * file_size  # Need to insert file size
        client_sock.sendall(payload)
        print(f"DBG: Sent response of length: {len(payload)}")
    except Exception as e:
        (f"Error processing TCP client request: {e}")


def run_udp_server(udp_port) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, udp_port))
    while True:
        raw_data, client_addr = sock.recvfrom(BUFFER_SIZE)
        payload_thread = threading.Thread(
            target=send_payload_udp,
            args=(client_addr, raw_data)
        ).start()


def send_payload_udp(client_addr, data) -> None:
    file_size = parsed_message_request(data)
    packets_num = math.ceil(file_size/PACKET_SIZE)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    for seq in range(packets_num):
        start_index = seq * PACKET_SIZE
        remaining = file_size - start_index
        next_packet_size = min(remaining, PACKET_SIZE)
        file = b"a" * next_packet_size

        # Building the massage by format
        payload = build_payload_message_udp(packets_num, seq, file)

        sock.sendto(payload, client_addr)
        print(f"DBG: Sent response of length: {len(payload)}")





if __name__ == "__main__":
    main()