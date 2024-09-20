import socket
import json

def send_udp_broadcast(message, port=10000):

    # address
    broadcast_address = ('<broadcast>', port)

    # create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    try:

        # message convert to string, json_str convert to json object
        json_obj = json.loads(json.dumps(message))

        # data value
        text_data = json_obj['data']
        print(f"json.data: {text_data}")

        # encoded to UTF-8
        text_bytes = text_data.encode('utf-8')

        # broadcast
        sock.sendto(text_bytes, broadcast_address)

    except Exception as e:
        print(f"broadcast error: {e}")
    finally:
        # close UDP socket
        sock.close()

# 使用示例
#if __name__ == "__main__":
#    send_udp_broadcast("Hello, this is a UDP broadcast message!")
