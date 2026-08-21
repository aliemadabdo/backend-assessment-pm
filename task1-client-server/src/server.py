import logging
import socket
import threading
from config import HOST, PORT, BUFFER_SIZE

logger = logging.getLogger(__name__)


class EchoServer:
    """A multi-threaded TCP echo server."""

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

        # Allows quick restart after the server exits (reuse address while in TIME_WAIT).
        self._server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen()

        # Makes stop() responsive when there are no incoming connections.
        self._server_socket.settimeout(0.5)

        logger.info("Server listening on %s:%s", self.host, self.port)

        try:
            while not self._stop_event.is_set():
                try:
                    client_socket, client_address = self._server_socket.accept()
                except socket.timeout:
                    continue  # just to check the stop event and continue the loop
                except OSError:
                    # Expected when stop() closes the listening socket.
                    if self._stop_event.is_set():
                        break
                    raise

                logger.info(
                    f"Client connected: {client_address[0]}:{client_address[1]}"
                )

                with self._lock:
                    self._client_sockets.add(client_socket)

                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address),
                    daemon=True,
                )

                with self._lock:
                    self._client_threads.append(client_thread)

                client_thread.start()

        finally:
            self._close_server_socket()
            self._close_client_sockets()

    def stop(self) -> None:
        """Stop accepting clients and close active connections."""
        self._stop_event.set()

        self._close_server_socket()
        self._close_client_sockets()

        with self._lock:
            threads = list(self._client_threads)

        for thread in threads:
            thread.join(timeout=2)

    def _handle_client(
        self,
        client_socket: socket.socket,
        client_address: tuple[str, int],
    ) -> None:
        """Handle messages from one client connection."""

        address = f"{client_address[0]}:{client_address[1]}"

        try:
            while not self._stop_event.is_set():
                try:
                    data = client_socket.recv(BUFFER_SIZE)
                except ConnectionResetError as e:
                    logger.info(f"Client {address} disconnected unexpectedly: {e}")
                    break

                if not data:
                    # recv() returning b"" means the peer performed an orderly shutdown.
                    logger.info(f"Client {address} disconnected")
                    break

                message = data.decode("utf-8")

                logger.info(
                    f"Message from {address}: {message}"
                )

                client_socket.sendall(data)

                if message == "exit":
                    break

        except Exception as e:
            logger.info(f"Client {address} disconnected unexpectedly: {e}")

        finally:
            with self._lock:
                # Needed because this can race with _close_client_sockets() during shutdown.
                self._client_sockets.discard(client_socket)

            try:
                client_socket.close()
            except OSError:
                pass

            logger.info(f"Connection closed: {address}")

    def _close_server_socket(self) -> None:
        if self._server_socket is None:
            return

        try:
            self._server_socket.close()
        except OSError:
            pass

        self._server_socket = None

    def _close_client_sockets(self) -> None:
        with self._lock:
            sockets = list(self._client_sockets)
            self._client_sockets.clear()

        for client_socket in sockets:
            try:
                # shutdown() can interrupt a blocking recv/accept, unlike close().
                client_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

            try:
                client_socket.close()
            except OSError:
                pass


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