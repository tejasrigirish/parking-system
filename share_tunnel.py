"""
Share Tunnel Launcher for Smart Parking Management System.
Starts the local Python server and creates a reliable, zero-config public HTTPS tunnel
via Cloudflare Tunnel (with fallback).
Extracts and prints the exact generated public URL in real time.
"""

import os
import sys
import time
import socket
import subprocess
import re
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED_EXE = os.path.join(BASE_DIR, "cloudflared.exe")
PORT = 5000

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

def ensure_cloudflared() -> bool:
    if os.path.exists(CLOUDFLARED_EXE) and os.path.getsize(CLOUDFLARED_EXE) > 1000000:
        return True
    
    print("Downloading Cloudflare Tunnel engine...", flush=True)
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    try:
        urllib.request.urlretrieve(url, CLOUDFLARED_EXE)
        return True
    except Exception as e:
        print(f"Failed to download cloudflared: {e}", flush=True)
        return False

def main():
    server_proc = None
    tunnel_proc = None

    # 1. Start local server if not already running
    if not is_port_in_use(PORT):
        cmd = [sys.executable, "-c", "from server import run_server; run_server(5000, open_browser=False)"]
        server_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=BASE_DIR
        )
        for _ in range(25):
            if is_port_in_use(PORT):
                break
            time.sleep(0.2)

    local_url = f"http://127.0.0.1:{PORT}"

    # 2. Ensure tunnel binary is present
    has_cf = ensure_cloudflared()
    public_url = None

    if has_cf:
        tunnel_proc = subprocess.Popen(
            [CLOUDFLARED_EXE, "tunnel", "--url", f"http://127.0.0.1:{PORT}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=BASE_DIR
        )

        url_regex = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
        for line in tunnel_proc.stdout:
            match = url_regex.search(line)
            if match:
                public_url = match.group(0)
                break
            if tunnel_proc.poll() is not None:
                break

    # Fallback to localtunnel if needed
    if not public_url:
        npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
        try:
            tunnel_proc = subprocess.Popen(
                [npx_cmd, "localtunnel", "--port", str(PORT)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=BASE_DIR
            )
            lt_regex = re.compile(r"https://[a-zA-Z0-9-]+\.loca\.lt")
            for line in tunnel_proc.stdout:
                match = lt_regex.search(line)
                if match:
                    public_url = match.group(0)
                    break
                if tunnel_proc.poll() is not None:
                    break
        except Exception:
            pass

    if public_url:
        print("========================================", flush=True)
        print("PARKING MANAGEMENT SYSTEM", flush=True)
        print()
        print("Local server:", flush=True)
        print(local_url, flush=True)
        print()
        print("Public URL:", flush=True)
        print(public_url, flush=True)
        print()
        print("Open this URL on another device:", flush=True)
        print(public_url, flush=True)
        print()
        print("Server is running...", flush=True)
        print("========================================", flush=True)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            if tunnel_proc:
                tunnel_proc.terminate()
            if server_proc:
                server_proc.terminate()
            sys.exit(0)
    else:
        print("Error: Could not generate a public tunnel URL.", flush=True)
        if tunnel_proc:
            tunnel_proc.terminate()
        if server_proc:
            server_proc.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()
