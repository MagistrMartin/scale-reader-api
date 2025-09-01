# pip install flask pyserial
from flask import Flask, jsonify, abort, json, request
from flask_cors import CORS
import re
import serial
import sys
import subprocess
import requests
import socket
from zebrafy import ZebrafyPDF

PORT = "COM3"
BAUDRATE = 9600

ser = serial.Serial(PORT, BAUDRATE)   # open once, keep open

app = Flask(__name__)
CORS(app)

def printOut(string):
    print(string, file=sys.stderr)

@app.route("/execute", methods=['POST'])
def execute():
    data = request.get_json(force=True, silent=True)
    if not data or 'command' not in data:
        return jsonify({"error":'JSON body missing "command" key'}), 400
    cmd = data['command']
    if not isinstance(cmd, list):
        return jsonify({"error":'"command" must be a list'}), 400

    try:
        result = subprocess.run(cmd,  capture_output=True, text=True, timeout=10)
        return jsonify({'stdout': result.stdout, 'stderr':result.stderr, 'returncode': result.returncode})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Command timed out'}), 408
    except Exception as e:
        return jsonify({'error': 'str(e)'}), 500

#@app.route("/git")
def pull_recent_changes():
    cmd = ['git', 'pull']
    result = subprocess.run(cmd,  capture_output=True, text=True, timeout=10)
    
#   return jsonify({'stdout': result.stdout, 'stderr':result.stderr, 'returncode': result.returncode})

@app.route("/print-packeta", methods=['POST'])
def print_packeta():
    order_id = request.args.get('orderId', type=int)
    if not order_id:
        return jsonify({"error": "orderId query param missing"}), 400

    import base64
    # 1. fetch PDF
    url = f"https://api.magistrmartin.cz/orders/packeta/printLabel?orderId={order_id}"
    try:
        pdf = requests.get(url, timeout=10).content
    except Exception as e:
        return jsonify({"error": f"download failed: {e}"}), 502

    if not pdf:
        return jsonify({"error": f"empty file: {e}"}), 502
    # 2. printer address (optional override in JSON body)
    host = "192.168.1.106"
    port = 9100

    # 3. send to printer

    try:
        with socket.create_connection((host, port), timeout=5) as s:
            s.sendall(ZebrafyPDF(base64.b64decode(pdf)).to_zpl())
            s.close()
        return jsonify({"status": "sent"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/weight")
def get_current_weight():
    buffer = ""
    buffer += ser.read(ser.in_waiting).decode()
    current_weight = 0

    if buffer:
        line = buffer.splitlines()[len(buffer.splitlines()) - 1]
        printOut(f"Line: {line}")
        match = re.search(r"Weight:\s*([-+]?\d+\.\d+)\s*kg", line, re.IGNORECASE)
        if match:
            current_weight = match.group(1)

    current_weight = int(float(current_weight)* 1000) 
    return jsonify({"current-weight": current_weight}) 

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000)
        pull_recent_changes()
    finally:
        ser.close()
