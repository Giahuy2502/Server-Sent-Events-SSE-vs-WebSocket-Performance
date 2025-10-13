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
        "throughput": round(sse_messages_sent / uptime if uptime > 0 else 0, 2)
    })

if __name__ == "__main__":
    print("Starting SSE Server on port 5000...")
    app.run(port=5000, debug=True, threaded=True)
