import logging
import socket
import threading
from config import BUFFER_SIZE, HOST, PORT

logger = logging.getLogger(__name__)


class EchoServer:

    def __init__(self, host: str = HOST, port: int = PORT):
        """Initialize the server with the given host and port."""
        self.host = host
        self.port = port

        self._server_socket: socket.socket | None = None
        self._client_sockets: set[socket.socket] = set()
        self._client_threads: list[threading.Thread] = []
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start accepting client connections."""

        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen()
        self._server_socket.settimeout(0.5)  # Makes stop() responsive when there are no incoming connections.
        
        logger.info("Server listening on %s:%s", self.host, self.port)

        while not self._stop_event.is_set():
            try:
                client_socket, client_address = self._server_socket.accept()
            except OSError:
                # Expected when stop() closes the listening socket.
                if self._stop_event.is_set():
                    break
                raise

            logger.info(
                f"Client connected: {client_address[0]}:{client_address[1]} | socket: {client_socket}"
            )

            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                logger.info("Client disconnected: %s:%s", client_address[0], client_address[1])
                client_socket.close()
                continue

            client_socket.sendall(data)

    def stop(self) -> None:
        """Stop accepting clients and close active connections."""
        # the clean up
        self._stop_event.set()
        self._close_client_sockets()
        self._close_server_socket()


    def _close_server_socket(self) -> None:
        """Close the server listening socket."""

        self._server_socket.close()



    def _close_client_sockets(self) -> None:
        """Close all active client connections."""

        for client_socket in self._client_sockets:
            client_socket.close()



def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    server = EchoServer()

    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.stop()


if __name__ == "__main__":
    main()