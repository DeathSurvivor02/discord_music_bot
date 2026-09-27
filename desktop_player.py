import os
import sys
import time
import socket
import threading
import webview

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def run_api_server():
    if not is_port_in_use(8000):
        print("[Desktop App] Starting local API audio engine on port 8000...")
        import uvicorn
        from api_server import app
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
    else:
        print("[Desktop App] API engine already active on port 8000.")

def main():
    # 1. Ensure backend API is active
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()

    # Give backend a moment to verify port
    time.sleep(1)

    # 2. Determine target player URL
    target_url = "http://localhost:8081"
    print(f"[Desktop App] Launching Spotify AI DJ Desktop Window -> {target_url}")

    # 3. Create native desktop window (uses Windows WebView2 engine)
    window = webview.create_window(
        title="Spotify AI DJ",
        url=target_url,
        width=460,
        height=880,
        resizable=True,
        min_size=(400, 600),
        background_color="#121212"
    )

    webview.start(private_mode=False)

if __name__ == "__main__":
    main()
