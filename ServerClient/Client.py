import concurrent.futures
import socket

import time
from Constants import (
    BROADCAST_PORT_TO, BUFFER_SIZE, UDP_TIMEOUT
)
from ServerClient.Message import parsed_message_offer, build_request_message, parsed_message_payload


def main():

    file_size, tcp_num, udp_num = start_up()
    print(f"Client started, listening for offer requests...")
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", BROADCAST_PORT_TO))
        # Keep Waiting for valid offer Message
        while True:
            offer_message, (server_ip, server_port) = sock.recvfrom(BUFFER_SIZE)
            print("Received offer from %s:%s" % (server_ip, server_port))
            try:
                udp_port, tcp_port = parsed_message_offer(offer_message)

                break
            except Exception as e:
                print(e)

        with concurrent.futures.ThreadPoolExecutor(max_workers=udp_num) as executor:
            udp_thread = [
                executor.submit(
                    run_udp,
                    server_ip=server_ip, udp_port=udp_port, file_size=file_size
                ) for _ in range(udp_num)
            ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=tcp_num) as executor:
            tcp_thread = [
                executor.submit(
                    run_tcp,
                    server_ip=server_ip, tcp_port=tcp_port, file_size=file_size
                ) for _ in range(tcp_num)
            ]

    print(f"All transfer completed")


def start_up():
    while True:
        try:
            file_size = int(input("Please enter file size (bytes): "))
            tcp_num = int(input("Please enter number of TCP connections: "))
            udp_num = int(input("Please Enter number of UDP connections: "))

            # Making sure user's input are valid
            if file_size <= 0 or tcp_num <= 0 or udp_num <= 0:
                raise ValueError()

            return file_size, tcp_num, udp_num

        except ValueError as e:
            print("Invalid input. Please enter positive integers only.")


def speed_test():
    pass


def run_udp(server_ip, udp_port, file_size):
    request_message = build_request_message(file_size)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", 0))  # port 0 means dynamic port allocation
        sock.sendto(request_message, (server_ip, udp_port))
        sock.settimeout(UDP_TIMEOUT)

        packet_acc = 0
        received_in_bytes = 0
        expected = 1

        start_time = time.time()
        while True:
            try:
                packet = sock.recv(BUFFER_SIZE)

                total_segment_count, curr_segment, payload = parsed_message_payload(packet)

                received_in_bytes += len(packet)
                packet_acc += 1
                expected = curr_segment + 1
            except socket.timeout:
                print("Socket timeout")
                break

        end_time = time.time()
        communication_time = end_time - start_time - UDP_TIMEOUT
        print(f"UDP got response from server, duration: {communication_time}")
        return communication_time, received_in_bytes, packet_acc, expected
    except Exception as e:
        print(e)


def run_tcp(server_ip, tcp_port, file_size):
    # request_message = build_request_message(file_size)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Client: trying to connect to {server_ip}:{tcp_port}")
    sock.connect((server_ip, tcp_port))
    sock.sendall(f"{file_size}\n".encode())

    start_time = time.time()
    response = sock.recv(file_size)
    end_time = time.time()
    duration_seconds = end_time - start_time
    print(f"TCP got response from server, duration: {duration_seconds}")

    return duration_seconds, len(response)


if __name__ == "__main__":
    main()
