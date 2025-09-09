# pip install flask pyserial
from flask import Flask, jsonify, abort, json, request
from flask_cors import CORS
import win32print
import subprocess
import requests

app = Flask(__name__)
CORS(app)

#@app.route("/git")
def pull_recent_changes():
    cmd = ['git', 'pull']
    result = subprocess.run(cmd,  capture_output=True, text=True, timeout=10)
    
#   return jsonify({'stdout': result.stdout, 'stderr':result.stderr, 'returncode': result.returncode})


def send_to_printer(zpl_data):
    # The exact printer name from Zebra Setup Utilities or Windows Control Panel
    printer_name = "ZDesigner ZD421-203dpi ZPL (kopie 1)"

    # A simple ZPL command to print "Hello Printer"
    # ^XA = Start of label
    # ^FO50,50 = Field Origin (position) at 50,50 dots
    # ^A0N,40,40 = Font
    # ^FD... = Field Data (the text to print)
    # ^FS = End of Field
    # ^XZ = End of label
    # zpl_data = b"""
    # ^XA
    # ^FO50,50^A0N,40,40^FDHello Printer^FS
    # ^XZ
    # """
    # zpl test data commented out in favour of coming as argument 

    try:
        # Open a handle to the printer
        h_printer = win32print.OpenPrinter(printer_name)
        h_job = win32print.StartDocPrinter(h_printer, 1, ("ZPL Print Job", None, "RAW"))
        win32print.StartPagePrinter(h_printer)
        win32print.WritePrinter(h_printer, zpl_data)
        win32print.EndPagePrinter(h_printer)
    except win32print.error as e:
        print(f"Error printing: {e}")
        print("Please check if the printer name is correct and the printer is online.")
        return jsonify({"error": f"Error printing: {e}"}), 502
    except Exception as e:
        return jsonify({"error": f"Error printing: {e}"}), 502
    finally:
        # Close the printer handle
        win32print.EndDocPrinter(h_printer)
        win32print.ClosePrinter(h_printer)
    return jsonify({"success": f"Successfully sent ZPL to {printer_name}"}), 200


@app.route("/print-packeta", methods=['POST'])
def print_packeta():
    order_id = request.args.get('orderId', type=int)
    dpi = request.args.get('dpi', type=int)
    if not order_id:
        return jsonify({"error": "orderId query param missing"}), 400
    if not dpi:
        return jsonify({"error": "dpi query param missing"}), 400

    # 1. fetch PDF
    url = f"https://api.magistrmartin.cz/orders/packeta/printLabelZpl?orderId={order_id}&dpi={dpi}"
    try:
        zpl_request = requests.get(url, timeout=10)
        zpl_request.raise_for_status()
    except Exception as e:
        return jsonify({"error": f"download failed: {e}"}), 502

    data = zpl_request.content
    if not data:
        return jsonify({"error": f"empty file: {e}"}), 502
    print('data: ',data)
    return send_to_printer(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    pull_recent_changes()
