import socket
import cv2
import numpy as np
import time
import pyautogui
import threading

# Server parameters
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 8181       # Change the port if needed
TARGET_FPS = 5   # Frames per second to aim for

# Create socket with reusable address
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)
print(f"Server started. Waiting for connections on port {PORT}...")

def handle_client(conn, addr):
    """Handle individual client connections."""
    print(f"Client connected: {addr}")
    frame_count = 0
    start_time = time.time()
    log_interval = 2  # Log every 2 seconds
    last_log_time = time.time()

    try:
        while True:
            # Capture the screen (center 600x600 region)
            screen_width, screen_height = pyautogui.size()
            left = (screen_width - 1024) // 2
            top = (screen_height - 768) // 2
            screenshot = pyautogui.screenshot(region=(left, top, 1024, 768))

            # Convert screenshot to numpy array
            frame = np.array(screenshot)

            # Convert RGB to BGR (OpenCV format)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)

            # Send frame to client
            conn.sendall(buffer.tobytes() + b'END')

            # Calculate FPS
            frame_count += 1
            current_time = time.time()
            elapsed_time = current_time - start_time
            
            # Control frame rate
            if TARGET_FPS > 0:
                time_to_sleep = max(0, (1.0 / TARGET_FPS) - (current_time - start_time))
                time.sleep(time_to_sleep)
            
            if elapsed_time > 1:
                fps = frame_count / elapsed_time
                frame_count = 0
                start_time = current_time

                # Log FPS and delay at the specified interval
                if current_time - last_log_time >= log_interval:
                    print(f"[{addr}] FPS: {fps:.2f}")
                    delay = elapsed_time * 1000  # milliseconds
                    print(f"[{addr}] Delay: {delay:.2f} ms")
                    last_log_time = current_time

            # Отображение кадра удалено, так как это было причиной дублирования

            # Close window on key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Stopping server on user request...")
                break

    except (ConnectionResetError, BrokenPipeError):
        print(f"Client {addr} disconnected.")
    except Exception as e:
        print(f"[ERROR] Unexpected error with client {addr}: {e}")
    finally:
        conn.close()
        print(f"Connection with {addr} closed.")

def main():
    """Main server loop."""
    try:
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            client_thread.start()
    except KeyboardInterrupt:
        print("Server stopped manually.")
    finally:
        server_socket.close()
        # cv2.destroyAllWindows() удалено, так как окно больше не создается
        print("Server stopped.")

if __name__ == "__main__":
    main()
