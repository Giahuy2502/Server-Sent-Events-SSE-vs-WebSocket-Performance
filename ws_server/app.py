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
    print(f"WebSocket client connected. Total connections: {ws_connections}, Client ID: {client_id}")
    
    # Send immediate confirmation
    socketio.emit("connected", {
        "status": "connected",
        "client_id": client_id,
        "server_type": "WebSocket"
    })
    
    # Send current stats to new client
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

# Handle connection errors
@socketio.on("connect_error")
def handle_connect_error(error):
    print(f"WebSocket connection error: {error}")

# Ping/Pong for latency testing
@socketio.on("ping")
def handle_ping(data):
    socketio.emit("pong", data)
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

# Fallback HTTP endpoints khi WebSocket không khả dụng
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

@app.route("/fallback")
def fallback_endpoint():
    """Endpoint fallback chính cho WebSocket"""
    global ws_messages_sent
    ws_messages_sent += 1
    
    return jsonify({
        "value": random.randint(0, 100),
        "timestamp": time.strftime("%H:%M:%S"),
        "message_id": ws_messages_sent,
        "send_time": time.time(),
        "fallback": True,
        "message": "Dữ liệu từ WebSocket fallback endpoint"
    })

@app.route("/fallback/polling")
def fallback_polling():
    """Long polling fallback cho WebSocket"""
    global ws_messages_sent
    messages = []
    
    # Tạo batch messages cho polling
    for i in range(3):
        ws_messages_sent += 1
        messages.append({
            "value": random.randint(0, 100),
            "timestamp": time.strftime("%H:%M:%S"),
            "message_id": ws_messages_sent,
            "send_time": time.time(),
            "fallback": True
        })
        time.sleep(0.3)
    
    return jsonify({
        "messages": messages,
        "count": len(messages),
        "fallback_type": "long_polling",
        "next_poll_delay": 1000  # milliseconds
    })

@app.route("/stream")
def fallback_stream():
    """HTTP stream fallback khi WebSocket thất bại"""
    def generate():
        global ws_messages_sent
        for i in range(10):  # Gửi 10 message rồi đóng
            ws_messages_sent += 1
            data = {
                "value": random.randint(0, 100),
                "timestamp": time.strftime("%H:%M:%S"),
                "message_id": ws_messages_sent,
                "send_time": time.time(),
                "fallback": True,
                "stream_position": i + 1
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(1)
        
        # Message kết thúc
        yield f"data: {json.dumps({'end': True, 'message': 'WebSocket fallback stream ended'})}\n\n"
    
    from flask import Response
    import json
    return Response(generate(), 
                   mimetype="text/plain",
                   headers={
                       'X-Fallback-Mode': 'websocket',
                       'Cache-Control': 'no-cache'
                   })

@app.route("/fallback/performance")
def fallback_performance():
    """Fallback performance monitoring"""
    global ws_connections, ws_messages_sent, ws_start_time
    
    # Lấy system metrics
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    uptime = time.time() - ws_start_time
    throughput = ws_messages_sent / uptime if uptime > 0 else 0
    
    return jsonify({
        "type": "performance",
        "connections": ws_connections,
        "messages_sent": ws_messages_sent,
        "throughput": round(throughput, 2),
        "cpu_usage": cpu_percent,
        "memory_usage": memory.percent,
        "uptime": round(uptime, 2),
        "timestamp": time.strftime("%H:%M:%S"),
        "fallback": True,
        "mode": "HTTP fallback"
    })

@app.route("/health")
def health_check():
    """Health check với thông tin fallback"""
    return jsonify({
        "status": "healthy",
        "server": "WebSocket",
        "timestamp": time.strftime("%H:%M:%S"),
        "connections": ws_connections,
        "messages_sent": ws_messages_sent,
        "uptime": round(time.time() - ws_start_time, 2),
        "fallback_available": True,
        "websocket_available": True
    })

@app.errorhandler(404)
def not_found(error):
    """Custom 404 handler với fallback info"""
    return jsonify({
        "error": "Endpoint không tìm thấy",
        "fallback_endpoints": [
            "/fallback",
            "/fallback/polling",
            "/fallback/stream", 
            "/fallback/performance",
            "/stats",
            "/health"
        ],
        "message": "WebSocket server hỗ trợ HTTP fallback"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 handler"""
    return jsonify({
        "error": "Lỗi server nội bộ",
        "fallback_available": True,
        "message": "Thử sử dụng endpoint /fallback"
    }), 500
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
