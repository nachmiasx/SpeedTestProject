import socket
import threading
import time

from Constants import (
    BROADCAST_PORT, BUFFER_SIZE, BROADCAST_IP, UDP_SERVER_PORT, TCP_SERVER_PORT
)


SERVER_IP = socket.gethostbyname(socket.gethostname())
BROADCAST_ADDR_TO = (BROADCAST_IP, BROADCAST_PORT) # This address is to sent to all localhost
BROADCAST_ADDR_FROM = (SERVER_IP, BROADCAST_PORT) # This is the address that the socket is on the server side

# Constant


def main():
    broadcast_thread = threading.Thread(
        target=broadcasting,
        kwargs=dict(udp_port=UDP_SERVER_PORT, tcp_port=TCP_SERVER_PORT)
    )

    udp_thread = threading.Thread(
        target=run_udp_server,
        kwargs=dict(udp_port=UDP_SERVER_PORT, tcp_port=TCP_SERVER_PORT)
    )

    tcp_thread = threading.Thread(
        target=run_tcp_server,
        kwargs=dict(udp_port=UDP_SERVER_PORT, tcp_port=TCP_SERVER_PORT)
    )

    print(f'Server started, listening on IP address {SERVER_IP}')
    tcp_thread.start()
    udp_thread.start()
    broadcast_thread.start()

    tcp_thread.join()
    udp_thread.join()
    broadcast_thread.join()

def broadcasting(udp_port, tcp_port) -> None:
    massage = b"Hello World!"
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(BROADCAST_ADDR_FROM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            sock.sendto(massage, BROADCAST_ADDR_TO)
            time.sleep(1)
            print("Broadcasting message") #NEED TO CHANGEEEEE
        except Exception as e:
            print(e) #NEED TO CHANGEEEE



def run_tcp_server() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(SERVER_IP, TCP_SERVER_PORT)
    sock.listen(5)
    while True:
        client_sock, client_addr = sock.accept()
        payload_thread = threading.Thread(
            target=sent_payload_tcp,
            args=(client_sock)
        ).start()


def sent_payload_tcp(client_sock):
    try:
        message: bytes = client_sock.recv(BUFFER_SIZE)
        # file_size = parse_request_message(message)
        print(f"DBG: Received filesize of {BUFFER_SIZE} bytes")

        file = b"a"  # Need to insert file size
        client_sock.sendall(file)
        print(f"DBG: Sent response of length: {len(file)}")
    except Exception as e:
        (f"Error processing TCP client request: {e}")




def run_udp_server() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(SERVER_IP, UDP_SERVER_PORT)
    while True:
        raw_data, client_addr = sock.recvfrom(BUFFER_SIZE)
        payload_thread = threading.Thread(
            target=send_payload_udp,
            args=(client_addr, raw_data)
        ).start()


def send_payload_udp(client_addr, data) -> None:
    # צריך לחלץ את גודל הקובץ מההודעה ואז לשלוח בהתאם מספר פקטות
    file_size = 1024
    packets_num = file_size//BUFFER_SIZE

    for seq in range(packets_num):
        start_index = seq * BUFFER_SIZE
        end_index = start_index + BUFFER_SIZE
        packet_data = data[start_index:end_index]
        # לבנות רגע את הבניה של ההודעה

    # try:
    #     # message: bytes = dtat.encode()
    #     # print(f"DBG: Sent request of length: {len(message)}")






if __name__ == "__main__":
    main()