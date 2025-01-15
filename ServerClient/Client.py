import concurrent
import socket
import threading
import time
from Constants import (
    BROADCAST_PORT, BUFFER_SIZE, BROADCAST_IP, UDP_SERVER_PORT, TCP_SERVER_PORT
)
from ServerClient.Message import pasred_message, create_request_message, parsed_payload


def main():
    # לשאול מחר אם גם הלקוח צריך לרוץ לעולם ובכל פעם לשאול גדלים או פעם אחת שואל ובכל הצעה שלוקח יוצר אותו מספר של tcp וudp
    file_size, tcp_num, udp_num = start_up()
    while True:
        # server_ip, tcp_port, udp_port = start_up()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("",BROADCAST_PORT))
        # Keep Waiting for valid offer Message
        while True:
            offer_message, (server_ip, server_port) = sock.recvfrom(BUFFER_SIZE)
            if valid_offer(offer_message):
                server_ip, tcp_port, udp_port = pasred_message(offer_message)
                break

        with concurrent.futures.ThreadPoolExecutor(max_workers=tcp_num) as executor:
            udp_thread = [
                executor.submit(
                    run_udp,
                    server_ip = server_ip, udp_port = udp_port, file_size = file_size
                ) for _ in range(udp_num)
            ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=tcp_num) as executor:
            udp_thread = [
                executor.submit(
                    run_tcp,
                    server_ip = server_ip, tcp_port = tcp_port, file_size = file_size
                ) for _ in range(tcp_num)
            ]


def start_up():
    while True:
        try:
            file_size = input("Please enter file size (bytes): ")
            tcp_num = input("Please enter number of TCP connections: ")
            udp_num = input("Please Enter number of UDP connections: ")

            # Making sure user's input are valid
            if not isinstance(file_size, int) or not isinstance(file_size, int) or not isinstance(file_size, int):
                raise ValueError()
            if file_size <= 0 or tcp_num <= 0 or udp_num <= 0:
                raise ValueError()

            return file_size, tcp_num, udp_num

        except ValueError as e:
            print("Invalid input. Please enter positive integers only.")


def waiting_for_offer():
    pass

def speed_test():
    pass

def run_udp(server_ip, udp_port, file_size):
    request_message = create_request_message(file_size)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", 0))  # port 0 means dynamic port allocation
        sock.sendto(request_message, (server_ip, udp_port))

        packet_acc = 0
        expected = 1
        received_in_bytes = 0

        start_time = time.time()
        while True:
            try:
                packet = sock.recv(BUFFER_SIZE)

                total_segment_count, curr_segment = parsed_payload(packet)
                # לסדר פה את הלוגיקה של מה אנחנו רוצים כדי לעשות את החישובים
                received_in_bytes += len(packet)
                packet_acc += 1
                expected = curr_segment+1
            except socket.timeout:
                break

        end_time = time.time()
        communication_time = end_time - start_time # אולי צרילך גם להוריד את הזמן שלקח לסוקט לקבל טיימאוט
        return communication_time, received_in_bytes, packet_acc, expected
    except Exception as e:
        print(e)



def run_tcp(server_ip, tcp_port, file_size):
    request_message = create_request_message(file_size)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_ip, tcp_port)

    sock.send(f"{file_size}\n".encode())
    start_time = time.time()

    response = sock.recv(file_size)  # צריך לוודא שאין בעיה לקבל הכל במכה אחת ואולי צריך לטפל בבעיות

    end_time = time.time()
    duration_seconds = end_time - start_time
    return duration_seconds, len(response)


def valid_offer(offer_message):
    #Need to insert logic
    return True

if __name__ == "__main__":
    start_up()