# pip install flask pyserial
from flask import Flask, jsonify, abort
import re
import serial

PORT = "COM5"
BAUDRATE = 9600

ser = serial.Serial(PORT, BAUDRATE, timeout=1)   # open once, keep open

app = Flask(__name__)

@app.route("/weight")
def get_current_weight():
    buffer = ""
    while ser.in_waiting:
        buffer += ser.read(ser.in_waiting).decode(errors="ignore")

    for line in buffer.splitlines():
        match = re.search(r"Weight:\s*([-+]?\d+\.\d+)\s*kg", line, re.IGNORECASE)
        if match:
            return jsonify({"current-weight": float(match.group(1))})

    abort(422)

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000)
    finally:
        ser.close()
