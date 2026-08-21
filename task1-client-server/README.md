# Task 1 — Multi-threaded Echo Server & Client

A TCP echo server that accepts multiple concurrent clients using a thread-per-connection
model, plus a small CLI client for interaction and manual testing.

![Server Architecture](img/server_arch.png)
*The server process at a glance: a listener/accept loop hands each connection to its own handler thread, backed by shared config and logging. Keep this picture in mind — every section below maps back to one of these components.*

## Overview

This project implements a basic TCP echo server in Python. The server accepts client
connections, echoes received messages back to the sender, and supports clean client
and server shutdown.

It uses **thread-per-connection**: each accepted client is handled by a dedicated
thread. This is simple to reason about and appropriate for small-scale/demo use —
see [Limitations](#limitations--suggestions) for what changes at higher scale.

## Features

- Echoes text messages back to the sending client
- Handles multiple concurrent clients using threads
- Graceful client disconnect handling and server shutdown
- Minimal dependencies — only the Python standard library required

## Quickstart

Follow along with the diagram below — it shows exactly this sequence: a client
connects, the server accepts and spawns a handler thread, the client sends a
message, and the server echoes it back.

![Multi-Threaded Echo Server Activity Flow](img/server_flow.png)
*Connect → handle → echo → disconnect, across one server thread and one client.*

**1. Start the server** (workspace root, one terminal):
```bash
python3 src/server.py
```

**2. Start one or more clients** (separate terminals, to simulate multiple concurrent
connections — each spawns its own handler thread on the server, as shown above):
```bash
python3 src/client.py
```

**3. Chat with the server.** In the client REPL, type a message and press Enter — the
server echoes it back. Type `exit` (or `quit`) to disconnect that client only; other
connected clients and the server keep running.

## Design Notes

- Default bind address: `127.0.0.1` (localhost). Default port: `65432`.
- Thread-per-connection: each accepted client connection is handled by a dedicated
  thread — the "Handler thread" box in the architecture diagram above. Easy to
  implement and reason about, but does not scale to very large numbers of
  simultaneous clients (see [Limitations](#limitations--suggestions)).
- The server logs actions to stdout for clarity during testing.

**Connection lifecycle** — every client connection moves through the same states,
regardless of how it ends (clean `exit`, abrupt disconnect, or server shutdown):

![State Machine](img/state_machine.png)
*LISTEN → CONNECTED → ECHO → CLOSE. If your implementation ever seems stuck or drops
messages, this is the diagram to check against — confirm which state the connection
is actually in versus where you expect it to be.*

## Protocol / Behavior

- Plaintext, line-based messages. The client sends a line; the server responds with
  the same line (see the ECHO state above).
- Client-side `exit` moves that client's connection to CLOSE and ends the client
  process — it has no effect on other clients or the server itself.

## Repository Layout

- `src/` — server and client source code (`server.py`, `client.py`, `config.py`)
- `img/` — the three diagrams referenced throughout this README:
  - `server_arch.png` — component view (used above, in Overview)
  - `server_flow.png` — activity/sequence flow (used above, in Quickstart)
  - `state_machine.png` — connection states (used above, in Design Notes)

## Configuration

Default host/port are defined in `src/config.py`. To accept connections from other
machines, change the host to `0.0.0.0` and ensure firewall rules allow the port —
this changes the "Clients" side of the architecture diagram (external connections
reaching the listener) but doesn't change the handler-thread model itself.

## Limitations & Suggestions

- Thread-per-connection is suitable for demo and small-scale testing. Each connection
  costs a full OS thread — under heavy concurrent load this exhausts system resources
  well before the architecture in the diagram above would need to change conceptually,
  just the "Handler thread" box's implementation.
- For higher concurrency, swap the accept loop for `selectors`, `asyncio`, or a
  bounded worker pool (`concurrent.futures.ThreadPoolExecutor`) — the architecture
  diagram's shape stays the same, only how the listener dispatches work changes.
- Server binds to `127.0.0.1` by default; bind to `0.0.0.0` only with appropriate
  security considerations for remote access.

## Notes on Original Draft

- Typos corrected (e.g. "standerd liberary" → "standard library", "exeception" →
  "exception").
- Binding to `localhost` is correct for local testing; use `0.0.0.0` only if external
  clients are intended, with the security note above.
- Ephemeral client port range `49152–65535` is standard OS behavior — no change
  needed.
- Each handler thread is scoped to exactly one accepted client socket; make sure
  cleanup runs on disconnect (see CLOSE state) to avoid leaking sockets/threads.