import socket

from config import HOST, PORT, BUFFER_SIZE



def run_client(host: str = HOST, port: int = PORT) -> None:
    """Connect to the echo server and exchange messages interactively."""

    # we use "with" and related context manager to ensure the socket is closed properly
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

            client_socket.sendall(message.encode("utf-8"))

            data = client_socket.recv(BUFFER_SIZE)

            if not data:
                print("Server closed the connection.")
                break

            print(f"Echo: {data.decode('utf-8')}")

            if message == "exit":
                break


if __name__ == "__main__":
    run_client()