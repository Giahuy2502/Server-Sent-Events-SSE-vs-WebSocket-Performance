from flask import Flask, Response, jsonify
from flask_cors import CORS
import time
import json
import random
import threading
import psutil
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Performance tracking variables
sse_connections = 0
sse_messages_sent = 0   
sse_start_time = time.time()

server_running = False

# Hàm này tạo ra dữ liệu ngẫu nhiên mỗi giây để gửi đến client.
def generate_data():
    global sse_messages_sent
    while True:
        # Generate random data
        data = {
            "value": random.randint(0, 100),
            "timestamp": time.strftime("%H:%M:%S"),
            "message_id": sse_messages_sent + 1,
            "send_time": time.time()
        }
        sse_messages_sent += 1
        yield f"data: {json.dumps(data)}\n\n"
        time.sleep(1)
# Hàm này thu thập và gửi đi các chỉ số hiệu năng của server mỗi 2 giây.
def generate_performance_data():
    global sse_connections, sse_messages_sent, sse_start_time
    while True:
        # Get system metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        uptime = time.time() - sse_start_time
        throughput = sse_messages_sent / uptime if uptime > 0 else 0
        
        performance_data = {
            "type": "performance",
            "connections": sse_connections,
            "messages_sent": sse_messages_sent,
            "throughput": round(throughput, 2),
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "uptime": round(uptime, 2),
            "timestamp": time.strftime("%H:%M:%S")
        }
        yield f"data: {json.dumps(performance_data)}\n\n"
        time.sleep(2)
# Client đăng ký nhận luồng dữ liệu ngẫu nhiên.
@app.route("/stream")
def stream():
    global sse_connections
    sse_connections += 1
    print(f"SSE Client connected. Total connections: {sse_connections}")
    
    def event_stream():
        global sse_connections
        try:
            for data in generate_data():
                yield data
        finally:
            sse_connections -= 1
            print(f"SSE Client disconnected. Total connections: {sse_connections}")
    
    return Response(event_stream(), mimetype="text/event-stream")
# cung cấp luồng dữ liệu về hiệu năng của server.
@app.route("/performance")
def performance_stream():
    return Response(generate_performance_data(), mimetype="text/event-stream")

@app.route("/stats")
def get_stats():
    global sse_connections, sse_messages_sent, sse_start_time
    uptime = time.time() - sse_start_time
    return jsonify({
        "server_type": "SSE",
        "connections": sse_connections,
        "messages_sent": sse_messages_sent,
        "uptime": round(uptime, 2),
        "throughput": round(sse_messages_sent / uptime if uptime > 0 else 0, 2),
        "current_value": random.randint(0, 100),
        "timestamp": time.strftime("%H:%M:%S"),
        "fallback_mode": True
    })

@app.route("/fallback")
def fallback_endpoint():
    """Fallback endpoint for when SSE EventSource fails"""
    return jsonify({
        "value": random.randint(0, 100),
        "timestamp": time.strftime("%H:%M:%S"),
        "message": "SSE fallback data",
        "fallback": True
    })

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "server": "SSE",
        "timestamp": time.strftime("%H:%M:%S"),
        "connections": sse_connections
    })

@app.route("/control/start", methods=['POST'])
def start_server():
    global server_running, sse_start_time
    server_running = True
    if sse_start_time == 0:
        sse_start_time = time.time()
    print("SSE Server STARTED")
    return jsonify({"status": "running", "message": "Server started"})

@app.route("/control/stop", methods=['POST'])
def stop_server():
    global server_running, sse_messages_sent
    server_running = False
    sse_messages_sent = 0
    print("SSE Server STOPPED")
    return jsonify({"status": "stopped", "message": "Server stopped"})

if __name__ == "__main__":
    print("Starting SSE Server on port 5000...")
    app.run(port=5000, debug=True, threaded=True)
