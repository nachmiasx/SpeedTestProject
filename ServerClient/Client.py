import concurrent.futures
import socket
import time
from Constants import (
    BROADCAST_PORT_TO, BUFFER_SIZE, UDP_TIMEOUT
)
from ServerClient.Message import parsed_message_offer, build_request_message, parsed_message_payload

# ANSI Colors for printing
RESET = "\033[0m"
GREEN = "\033[92m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"  # For UDP
BLUE = "\033[94m"  # For TCP
YELLOW = "\033[93m"
RED = "\033[91m"

def main():
    file_size, tcp_num, udp_num = start_up()
    print(f"{CYAN}Client started, listening for offer requests...{RESET}")
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", BROADCAST_PORT_TO))

        # Wait for a valid offer message
        while True:
            offer_message, (server_ip, server_port) = sock.recvfrom(BUFFER_SIZE)
            print(f"{MAGENTA}Received offer from {server_ip}:{server_port}{RESET}")
            try:
                udp_port, tcp_port = parsed_message_offer(offer_message)
                print(f"{MAGENTA}Parsed UDP Port: {udp_port}, TCP Port: {tcp_port}{RESET}")
                break
            except Exception as e:
                print(f"{RED}Invalid offer message: {e}{RESET}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=udp_num) as executor:
            udp_threads = [
                executor.submit(
                    run_udp,
                    server_ip=server_ip, udp_port=udp_port, file_size=file_size
                ) for _ in range(udp_num)
            ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=tcp_num) as executor:
            tcp_threads = [
                executor.submit(
                    run_tcp,
                    server_ip=server_ip, tcp_port=tcp_port, file_size=file_size
                ) for _ in range(tcp_num)
            ]

    print(f"{GREEN}All transfers completed{RESET}")


def start_up():
    while True:
        try:
            file_size = int(input(f"{YELLOW}Please enter file size (bytes): {RESET}"))
            tcp_num = int(input(f"{YELLOW}Please enter number of TCP connections: {RESET}"))
            udp_num = int(input(f"{YELLOW}Please Enter number of UDP connections: {RESET}"))

            # Validate input
            if file_size <= 0 or tcp_num <= 0 or udp_num <= 0:
                raise ValueError()

            return file_size, tcp_num, udp_num

        except ValueError as e:
            print(f"{RED}Invalid input. Please enter positive integers only.{RESET}")


def run_udp(server_ip, udp_port, file_size):
    request_message = build_request_message(file_size)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", 0))  # Port 0 means dynamic port allocation
        print(f"{MAGENTA}UDP client started...{RESET}")
        sock.sendto(request_message, (server_ip, udp_port))
        print(f"{MAGENTA}UDP sent request to {server_ip}:{udp_port}{RESET}")
        sock.settimeout(UDP_TIMEOUT)

        packet_acc = 0
        received_in_bytes = 0
        expected_packets = 1

        start_time = time.time()
        while True:
            try:
                packet = sock.recv(BUFFER_SIZE)
                total_segment_count, curr_segment, payload = parsed_message_payload(packet)

                received_in_bytes += len(packet)
                packet_acc += 1
                expected_packets = total_segment_count

                print(f"{MAGENTA}[UDP Packet] Received segment {curr_segment+1}/{total_segment_count}{RESET}")
            except socket.timeout:
                print(f"{RED}[UDP] Socket timeout. Stopping reception.{RESET}")
                break

        end_time = time.time()
        communication_time = end_time - start_time - UDP_TIMEOUT

        packet_loss = ((expected_packets - packet_acc) / expected_packets) * 100 if expected_packets > 0 else 0

        print(f"{MAGENTA}UDP Communication Summary:{RESET}")
        print(f"{MAGENTA}  - Duration: {communication_time} seconds{RESET}")
        print(f"{MAGENTA}  - Packets Received: {packet_acc}/{expected_packets}{RESET}")
        print(f"{MAGENTA}  - Bytes Received: {received_in_bytes} bytes{RESET}")
        print(f"{MAGENTA}  - Packet Loss/Corruption: {packet_loss:.2f}%{RESET}")

        return communication_time, received_in_bytes, packet_acc, expected_packets

    except Exception as e:
        print(f"{RED}[UDP ERROR] {e}{RESET}")


def run_tcp(server_ip, tcp_port, file_size):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"{BLUE}TCP client trying to connect to {server_ip}:{tcp_port}{RESET}")
        sock.connect((server_ip, tcp_port))
        print(f"{BLUE}TCP client connected{RESET}")
        sock.sendall(f"{file_size}\n".encode())
        print(f"{BLUE}TCP client sent request for {file_size} bytes{RESET}")

        start_time = time.time()
        response = sock.recv(file_size)
        end_time = time.time()

        duration_seconds = end_time - start_time
        received_bytes = len(response)

        print(f"{BLUE}TCP Communication Summary:{RESET}")
        print(f"{BLUE}  - Duration: {duration_seconds} seconds{RESET}")
        print(f"{BLUE}  - Bytes Received: {received_bytes}/{file_size} bytes{RESET}")

        return duration_seconds, received_bytes

    except Exception as e:
        print(f"{RED}[TCP ERROR] {e}{RESET}")


if __name__ == "__main__":
    main()
