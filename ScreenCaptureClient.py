import socket, cv2, numpy as np, time, threading, signal, os, base64

SERVER_IP, SERVER_PORT, running, connected, client_socket, data_buffer = '80.92.211.176', 8181, True, False, None, b''
base64_image_data = "iVBORw0KGgoAAAANSUhEUgAAADAAAAAlAQAAAAAsYlcCAAAACklEQVR4AWMYBQABAwABRUEDtQAAAABJRU5ErkJggg=="

def signal_handler(signum, frame):
    global running
    running = False

def connect_to_server():
    global connected, client_socket
    try:
        if client_socket:
            client_socket.close()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        client_socket.connect((SERVER_IP, SERVER_PORT))
        connected = True
    except socket.error:
        connected = False
        time.sleep(5)

def receive_video():
    global data_buffer, connected, running, client_socket
    fallback_frame = cv2.imdecode(np.frombuffer(base64.b64decode(base64_image_data), np.uint8), cv2.IMREAD_COLOR)
    cv2.namedWindow('Video Stream', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Video Stream', 1024, 768)
    while running:
        if not connected:
            connect_to_server()
            data_buffer = b''
            continue
        try:
            data = client_socket.recv(16384)
            if not data:
                connected = False
                cv2.imshow('Video Stream', fallback_frame)
                if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('Video Stream', cv2.WND_PROP_VISIBLE) < 1:
                    running = False
                    break
                time.sleep(1)
                continue
            data_buffer += data
            while b'END' in data_buffer and running:
                frame_data, data_buffer = data_buffer.split(b'END', 1)
                frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    cv2.imshow('Video Stream', frame)
                if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('Video Stream', cv2.WND_PROP_VISIBLE) < 1:
                    running = False
                    break
        except socket.error:
            connected = False
            time.sleep(1)
    shutdown()

def shutdown():
    global client_socket, running
    running = False
    if client_socket:
        try:
            client_socket.close()
        except Exception:
            pass
    cv2.destroyAllWindows()
    os._exit(0)

def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    t = threading.Thread(target=receive_video, daemon=True)
    t.start()
    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()

if __name__ == "__main__":
    main()
