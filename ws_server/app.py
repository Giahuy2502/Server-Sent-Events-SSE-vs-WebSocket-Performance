from flask import Flask
from flask_socketio import SocketIO
import random, time, threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

def generate_data():
    print("WebSocket data generator started")
    while True:
        data = {
            "value": random.randint(0, 100),
            "timestamp": time.strftime("%H:%M:%S")
        }
        socketio.emit("update", data)
        print(f"WS Emitted: {data}")
        time.sleep(1)

@socketio.on("connect")
def handle_connect():
    print("WebSocket client connected")

@socketio.on("disconnect")
def handle_disconnect():
    print("WebSocket client disconnected")

if __name__ == "__main__":
    threading.Thread(target=generate_data, daemon=True).start()
    socketio.run(app, host="127.0.0.1", port=8080, debug=True)
