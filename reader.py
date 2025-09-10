# pip install flask pyserial
from flask import Flask, jsonify, abort, json, request
from flask_cors import CORS
import re
import serial
import sys
import subprocess
import requests
import datetime


BAUDRATE = 9600


def log(text):
    with open("logs.txt", "a") as file:
        file.write(str(datetime.datetime.now()) + ":" + text)
   # open once, keep open
def establish_connection():
    ports = ["COM1", "COM2", "COM3", "COM4", "COM5"]
    ser = serial.Serial()
    ser.baudrate = BAUDRATE
    for p in ports:
        try:
            ser.port = p
            ser.open()
            if ser.is_open:
                print(f"Successful connection on port {p}")
                return ser
        except serial.serialutil.SerialException as e:
            print(f"Failed to open on port {p}")
            return None
    return None    


app = Flask(__name__)
CORS(app)


@app.route("/git")
def pull_recent_changes():
    cmd = ['git','restore', '--staged', '.']
    subprocess.run(cmd,  capture_output=True, text=True, timeout=10)
    cmd = ['git', 'restore', '.']
    subprocess.run(cmd,  capture_output=True, text=True, timeout=10)
    cmd = ['git', 'pull']
    result = subprocess.run(cmd,  capture_output=True, text=True, timeout=10)
    log(result.stdout + result.stderr)
#   return jsonify({'stdout': result.stdout, 'stderr':result.stderr, 'returncode': result.returncode})

@app.route("/weight")
def get_current_weight():
    try:
        buffer = ""
        buffer += ser.read(ser.in_waiting).decode()
        current_weight = 0

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

if __name__ == "__main__":
    pull_recent_changes()
    ser = establish_connection()
    if ser is None:
        log("Failed to establish connection")
    else:
        log(f"Connection successfull to port {ser.port}")
    try:
        app.run(host="0.0.0.0", port=5000)
    finally:
        ser.close()
