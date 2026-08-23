import socket

from config import HOST, MSG_POSTFIX, MSG_PREFIX, PORT, BUFFER_SIZE


def send_with_framing(sock: socket.socket, msg: str) -> None:
    """Send a message with prefix and postfix to indicate boundaries, handling arbitrary length."""
    payload = f"{MSG_PREFIX}{msg}{MSG_POSTFIX}".encode("utf-8")
    totalsent = 0
    while totalsent < len(payload):
        sent = sock.send(payload[totalsent:])
        if sent == 0:
            raise RuntimeError("Socket connection broken during send.")
        totalsent += sent

def recv_with_framing(sock: socket.socket) -> str:
    """
    Receive data until a message with both prefix and postfix is received,
    handling messages that might exceed the buffer size.
    """
    buffer = b""
    while True:
        chunk = sock.recv(BUFFER_SIZE)
        if not chunk:
            # Server closed connection
            return ""
        buffer += chunk
        start = buffer.find(MSG_PREFIX.encode("utf-8"))
        end = buffer.find(MSG_POSTFIX.encode("utf-8"), start + len(MSG_PREFIX))
        if start != -1 and end != -1:
            # Found full framed message
            msg_start = start + len(MSG_PREFIX)
            msg_end = end
            full_msg = buffer[msg_start:msg_end].decode("utf-8")
            # Remove up to end of postfix from buffer for next message (not really needed for echo)
            buffer = buffer[end + len(MSG_POSTFIX):]
            return full_msg

def run_client(host: str = HOST, port: int = PORT) -> None:
    """Connect to the echo server and exchange messages interactively."""

    # We use "with" and related context manager to ensure the socket is closed properly
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        # OS automatically picks an available ephemeral port (an implicit bind)
        client_socket.connect((host, port))

        print(f"Connected to {host}:{port}")
        print("Type messages to send to the server.")
        print("Type 'exit' to close the connection.")

        while True:
            try:
                message = input("> ")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...\n")
                break

            if not message:
                continue

            send_with_framing(client_socket, message)

            echo = recv_with_framing(client_socket)

            if echo == "":
                print("Server closed the connection.")
                break

            print(f"Echo: {echo}")

            if message == "exit":
                break


if __name__ == "__main__":
    run_client()