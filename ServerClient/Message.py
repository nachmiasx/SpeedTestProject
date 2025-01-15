import struct

from Constants import MAGIC_COOKIE, CODES


def _valid_message(magic_cookie, type, message_type):
    if magic_cookie != MAGIC_COOKIE:
        return False
    if CODES.get(type) != message_type:
        return False
    return True

def parsed_message_offer(offer_message):
        if len(offer_message) != 9:
            raise ValueError("Offer message incorrect length")

        cookie, message_type, udp_port, tcp_port = struct.unpack('>IBHH', offer_message)

        if _valid_message(cookie, "offer", message_type):
            raise ValueError("Corrupted offer message")

        return udp_port, tcp_port

def parsed_message_request(request_message):
    if len(request_message) != 13:
        raise ValueError("Request message incorrect length")

    cookie, message_type, file_size = struct.unpack('>IBQ', request_message)

    if _valid_message(cookie, "request", message_type):
        raise ValueError("Corrupted request message")
    if file_size <= 0:
        raise ValueError("Request file size is invalid")

    return file_size


def parsed_message_payload(payload_message):
    if len(payload_message) < 21:
        raise ValueError("Payload message incorrect length")

    cookie, message_type, total_segment_count, current_count = struct.unpack('>IBQ', payload_message[:21])
    message_body = payload_message[21:]

    if current_count > total_segment_count:
        raise ValueError("Message is corrupt, current segment count is greater than total segment count")

    if _valid_message(cookie, "payload", message_type):
        raise ValueError("Corrupted payload message")

    #להוסיף בדיקה שבוקת שההודעה שהגיעה אכן הגיעה בגודל הרצוי וגם לשים לב ללוגיקה בין הפרוטוקולים

    return total_segment_count, current_count, message_body

def build_offer_message(udp_port, tcp_port):
    """
    Build an offer message.
    Format: Magic cookie (4 bytes), Message type (1 byte), Server UDP port (2 bytes), Server TCP port (2 bytes)
    """
    message_type = CODES["offer"]  # Should be 0x2
    return struct.pack('>IBHH', MAGIC_COOKIE, message_type, udp_port, tcp_port)

def build_request_message(file_size):
    """
    Build a request message.
    Format: Magic cookie (4 bytes), Message type (1 byte), File size (8 bytes)
    """
    message_type = CODES["request"]  # Should be 0x3
    return struct.pack('>IBQ', MAGIC_COOKIE, message_type, file_size)

def build_payload_message_udp(total_segment_count, current_segment_count, payload):
    """
    Build a payload message.
    Format: Magic cookie (4 bytes), Message type (1 byte),
            Total segment count (8 bytes), Current segment count (8 bytes), Payload (variable length)
    """
    message_type = CODES["payload"]  # Should be 0x4
    header = struct.pack('>IBQQ', MAGIC_COOKIE, message_type, total_segment_count, current_segment_count)
    return header + payload
