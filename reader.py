# pip install flask pyserial
from flask import Flask, jsonify, abort, json, request
from flask_cors import CORS
import re
import serial
import sys
import os
import subprocess

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
