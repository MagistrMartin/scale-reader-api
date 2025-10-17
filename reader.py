# pip install flask pyserial
import asyncio
import datetime
import re
import subprocess

import serial
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

BAUDRATE = 9600

app = Flask(__name__)
CORS(app)
sio  = SocketIO(app, cors_allowed_origins="*", async_mode="threading")  # or "eventlet"/"gevent"

def log(msg):
    with open("logs.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()} : {msg}\n")

def establish_connection():
    ports = ["COM1", "COM2", "COM3", "COM4", "COM5"]
    ser = serial.Serial()
    ser.baudrate = BAUDRATE
    for p in ports:
        try:
            ser.port = p
            ser.open()
            if ser.is_open:
                log(f"Successful connection on port {p}")
                return ser
        except serial.SerialException as e:
            log(f"Failed to open on port {p}. Error {e}")
            return None
    return None


def pull_recent_changes():
    cmd = ['git','restore', '--staged', '.']
    result = subprocess.run(cmd,  capture_output=True, text=True, timeout=10)
    log(result.stdout + result.stderr)
    cmd = ['git', 'restore', '.']
    result = subprocess.run(cmd,  capture_output=True, text=True, timeout=10)
    log(result.stdout + result.stderr)
    cmd = ['git', 'pull']
    result = subprocess.run(cmd,  capture_output=True, text=True, timeout=100)
    log(result.stdout + result.stderr)
    cmd = ['pip', 'install', '-r', 'requirements.txt']
    result = subprocess.run(cmd,  capture_output=True, text=True, timeout=100)
    log(result.stdout + result.stderr)

@app.route("/weight")
def get_current_weight():
    try:
        buffer = ""
        buffer += ser.read(ser.in_waiting).decode()
        current_weight = 0

        if not buffer:
            # Empty buffer comes back as 204
            sio.emit("scale_reading", {"weight": 0})  # broadcast to everyone
            return jsonify({}), 204

        if buffer:
            line = buffer.splitlines()[len(buffer.splitlines()) - 1]
            match = re.search(r"Weight:\s*([-+]?\d+\.\d+)\s*kg", line, re.IGNORECASE)
            if match:
                current_weight = match.group(1)

        current_weight = int(float(current_weight)* 1000)
        return jsonify({"current-weight": current_weight}), 200
    except Exception as e:
        log("Error in getting weight: " + e)
        return jsonify({"error": f"Error printing: {e}"}), 502

@sio.on('connect')
def handle_connect():
    print('Client connected')

@sio.on('message')
def handle_message(data):
    print('Received message:', data)
    sio.emit('response', 'Server received your message: ' + data)

# ----------------  background job  ----------------
async def scale_emitter():
    while True:
        buffer = ""
        buffer += ser.read(ser.in_waiting).decode()
        current_weight = 0

        if not buffer:
            # Empty buffer comes back as 204
            sio.emit("scale_reading", {"weight": 0})  # broadcast to everyone
            return jsonify({}), 204

        if buffer:
            line = buffer.splitlines()[len(buffer.splitlines()) - 1]
            match = re.search(r"Weight:\s*([-+]?\d+\.\d+)\s*kg", line, re.IGNORECASE)
            if match:
                current_weight = match.group(1)

        current_weight = int(float(current_weight)* 1000)
        sio.emit("scale_reading", {"weight": current_weight})  # broadcast to everyone
        await asyncio.sleep(0.3)
        # val = random.randint(0, 100)
        # print(val)
        # sio.emit("scale_reading", {"weight": val})  # broadcast to everyone

def _loop():
    asyncio.run(scale_emitter())


if __name__ == "__main__":
    pull_recent_changes()
    ser = establish_connection()
    if ser is None:
        log("Failed to establish connection")
    else:
        log(f"Connection successfull to port {ser.port}")

    sio.start_background_task(_loop)


    sio.run(app, host="0.0.0.0", port=5000 )
    # finally:
    #     ser.close()
