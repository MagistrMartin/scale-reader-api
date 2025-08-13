import re
import serial
from fastapi import FastAPI
from contextlib import asynccontextmanager

PORT = "COM5"
BAUDRATE = 9600

ser = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ser
    ser = serial.Serial(PORT, BAUDRATE, timeout=0)
    yield
    ser.close()


app = FastAPI(lifespan=lifespan)


@app.get("/current-weight")
def get_current_weight():
    buffer = ""
    while ser.in_waiting:
        buffer += ser.read(ser.in_waiting).decode(errors="ignore")

    for line in buffer.splitlines():
        match = re.search(r"Weight:\s*([-+]?\d+\.\d+)\s*kg", line, re.IGNORECASE)
        if match:
            return {"current-weight": float(match.group(1))}

    return {"current-weight": None}

