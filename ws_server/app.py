from flask import Flask, jsonify, request
from flask_socketio import SocketIO
import random, time, threading
import psutil
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Performance tracking variables
ws_connections = 0
ws_messages_sent = 0
ws_start_time = time.time()
connected_clients = set()

server_running = False
# Hàm này mô phỏng việc tạo ra dữ liệu ngẫu nhiên
def generate_data():
    global ws_messages_sent, server_running
    print("WebSocket data generator started")
    while True:
        data = {
            "type": "data",
            "value": random.randint(0, 100),
            "timestamp": time.strftime("%H:%M:%S"),
            "message_id": ws_messages_sent + 1,
            "send_time": time.time()
        }
        ws_messages_sent += 1
        socketio.emit("update", data)
        print(f"WS Emitted: {data}")
        time.sleep(1)
# Hàm này thu thập các chỉ số hiệu năng của server và gửi chúng đi mỗi 2 giây.
def generate_performance_data():
    global ws_connections, ws_messages_sent, ws_start_time
    while True:
        # Get system metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        uptime = time.time() - ws_start_time
        throughput = ws_messages_sent / uptime if uptime > 0 else 0
        
        performance_data = {
            "type": "performance",
            "connections": ws_connections,
            "messages_sent": ws_messages_sent,
            "throughput": round(throughput, 2),
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "uptime": round(uptime, 2),
            "timestamp": time.strftime("%H:%M:%S")
        }
        socketio.emit("performance", performance_data)
        print(f"WS Performance: {performance_data}")
        time.sleep(2)

@socketio.on("start_server")
def handle_start_server():
    global server_running, ws_start_time, ws_connections
    if(server_running == False):
        ws_connections += 1
    server_running = True
    if ws_start_time == 0:
        ws_start_time = time.time()
    socketio.emit("server_started", {"status": "running"})
    print("WebSocket Server started")


@socketio.on("stop_server")
def handle_stop_server():
    global server_running
    if(server_running == True):
        ws_connections -= 1
    server_running = False
    socketio.emit("server_stopped", {"status": "stopped"})
    print("WebSocket Server stopped")

# Hàm này tự động được gọi ngay khi có một client mới kết nối thành công.
@socketio.on("connect")
def handle_connect():
    global ws_connections
    ws_connections += 1
    client_id = str(len(connected_clients) + 1)
    connected_clients.add(client_id)
    print(f"WebSocket client connected. Total connections: {ws_connections}")
    
    # Send current stats to   new client
    socketio.emit("stats", {
        "server_type": "WebSocket",
        "connections": ws_connections,
        "messages_sent": ws_messages_sent,
        "client_id": client_id
    })
# Tự động được gọi khi một client ngắt kết nối
@socketio.on("disconnect")
def handle_disconnect():
    global ws_connections
    ws_connections -= 1
    print(f"WebSocket client disconnected. Total connections: {ws_connections}")
# Được gọi khi client gửi sự kiện "get_stats"``
@socketio.on("get_stats")
def handle_get_stats():
    global ws_connections, ws_messages_sent, ws_start_time
    uptime = time.time() - ws_start_time
    stats = {
        "server_type": "WebSocket",
        "connections": ws_connections,
        "messages_sent": ws_messages_sent,
        "uptime": round(uptime, 2),
        "throughput": round(ws_messages_sent / uptime if uptime > 0 else 0, 2)
    }
    socketio.emit("stats", stats)

# Fallback HTTP endpoints for when WebSocket is not available
@app.route("/stats")
def get_stats_http():
    global ws_connections, ws_messages_sent, ws_start_time
    uptime = time.time() - ws_start_time
    return jsonify({
        "server_type": "WebSocket",
        "connections": ws_connections,
        "messages_sent": ws_messages_sent,
        "uptime": round(uptime, 2),
        "throughput": round(ws_messages_sent / uptime if uptime > 0 else 0, 2),
        "current_value": random.randint(0, 100),
        "timestamp": time.strftime("%H:%M:%S"),
        "fallback_mode": True
    })

@app.route("/stream")
def fallback_stream():
    """HTTP endpoint for fallback when WebSocket fails"""
    def generate():
        global ws_messages_sent
        for i in range(10):  # Send 10 messages then close
            data = {
                "value": random.randint(0, 100),
                "timestamp": time.strftime("%H:%M:%S"),
                "message_id": ws_messages_sent + 1,
                "fallback": True
            }
            ws_messages_sent += 1
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(1)
    
    from flask import Response
    import json
    return Response(generate(), mimetype="text/plain")
# Được gọi khi client gửi sự kiện "ping" kèm theo một timestamp
@socketio.on("ping")
def handle_ping(data):
    # Send back pong with timestamp for latency calculation
    socketio.emit("pong", {
        "client_time": data.get("timestamp"),
        "server_time": time.time()
    })


if __name__ == "__main__":
    print("Starting WebSocket Server on port 8080...")
    # Start data generator
    threading.Thread(target=generate_data, daemon=True).start()
    # Start performance monitor
    threading.Thread(target=generate_performance_data, daemon=True).start()
    
    socketio.run(app, host="127.0.0.1", port=8080, debug=True)
