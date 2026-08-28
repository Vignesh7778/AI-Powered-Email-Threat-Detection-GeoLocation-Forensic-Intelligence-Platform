import os
import sys
import socket
import subprocess
import uvicorn

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0

def kill_process_on_port(port: int):
    """Attempt to free the port on Windows if occupied by a stale process."""
    try:
        cmd = f"netstat -ano | findstr :{port}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5 and "LISTENING" in parts:
                    pid = parts[-1]
                    if pid.isdigit() and int(pid) != os.getpid() and int(pid) != 0:
                        print(f"[*] Terminating conflicting process on port {port} (PID: {pid})...")
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
    except Exception as e:
        print(f"[!] Warning while attempting to free port {port}: {e}")

def main():
    preferred_port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")

    print("=" * 60)
    print(f"[*] Checking port assignment for {host}:{preferred_port}...")

    if is_port_in_use(preferred_port, host):
        print(f"[!] Port {preferred_port} is currently in use. Attempting to free it...")
        kill_process_on_port(preferred_port)

    # Double check if port is now free
    if is_port_in_use(preferred_port, host):
        print(f"[!] Could not free port {preferred_port}. Searching for next available port...")
        while is_port_in_use(preferred_port, host):
            preferred_port += 1
        print(f"[+] Found available port: {preferred_port}")
    else:
        print(f"[+] Port {preferred_port} is clear and ready!")

    print(f"[*] Starting FastAPI AI/ML Microservice on http://{host}:{preferred_port}")
    print(f"[*] Swagger Docs URL: http://{host}:{preferred_port}/docs")
    print(f"[*] ReDoc Docs URL:   http://{host}:{preferred_port}/redoc")
    print("=" * 60)

    uvicorn.run("app.main:app", host=host, port=preferred_port, reload=True)

if __name__ == "__main__":
    main()

