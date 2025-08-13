# pip install flask pyserial
from flask import Flask, jsonify
import re
import serial

PORT = "COM5"
BAUDRATE = 9600

ser = serial.Serial(PORT, BAUDRATE, timeout=0)
ser.close()

app = Flask(__name__)

@app.route("/weight")
def get_current_weight():
    buffer = ""
    ser.open()
    while ser.in_waiting:
        buffer += ser.read(ser.in_waiting).decode(errors="ignore")
    ser.close()

    for line in buffer.splitlines():
        match = re.search(r"Weight:\s*([-+]?\d+\.\d+)\s*kg", line, re.IGNORECASE)
        if match:
            return jsonify({"current-weight": float(match.group(1))})

    return jsonify({"current-weight": None})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)