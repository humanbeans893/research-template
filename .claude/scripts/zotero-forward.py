"""WSL2 -> Windows Zotero port forwarder.

Forwards localhost:23119 to the Windows host gateway so that
pyzotero (which hardcodes 127.0.0.1:23119) can reach the Zotero
desktop app running on the Windows side.
"""

import socket
import select
import subprocess
import threading
import sys


def get_windows_gateway() -> str:
    """Get the Windows host IP from the default route."""
    result = subprocess.run(
        ["ip", "route", "show", "default"],
        capture_output=True, text=True, check=True,
    )
    # e.g. "default via 172.30.224.1 dev eth0"
    return result.stdout.split()[2]


def forward(src: socket.socket, dst: socket.socket) -> None:
    try:
        while True:
            r, _, _ = select.select([src], [], [], 1.0)
            if r:
                data = src.recv(65536)
                if not data:
                    break
                dst.sendall(data)
    except Exception:
        pass
    finally:
        for s in (src, dst):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            s.close()


def main() -> None:
    port = 23119
    gateway = get_windows_gateway()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("127.0.0.1", port))
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"Port {port} already in use — forwarder is already running.", flush=True)
            sys.exit(0)
        raise
    server.listen(5)
    print(f"Forwarding localhost:{port} -> {gateway}:{port}", flush=True)

    while True:
        client, _ = server.accept()
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote.settimeout(10)
        remote.connect((gateway, port))
        remote.settimeout(None)
        threading.Thread(target=forward, args=(client, remote), daemon=True).start()
        threading.Thread(target=forward, args=(remote, client), daemon=True).start()


if __name__ == "__main__":
    main()
