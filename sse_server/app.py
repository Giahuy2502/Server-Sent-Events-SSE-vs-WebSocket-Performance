from flask import Flask, Response
from flask_cors import CORS
import time
import json
import random

app = Flask(__name__)
CORS(app)

def generate_data():
    while True:
        data = {
            "value": random.randint(0, 100),
            "timestamp": time.strftime("%H:%M:%S")
        }
        yield f"data: {json.dumps(data)}\n\n"
        time.sleep(1)

@app.route("/stream")
def stream():
    return Response(generate_data(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
