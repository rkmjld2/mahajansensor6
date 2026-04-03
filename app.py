from flask import Flask, request, jsonify, render_template
import os
from datetime import datetime
import csv
import json

app = Flask(__name__)

DATA_FILE = "data/sensor_data.csv"
STATUS_FILE = "data/status.json"

# Ensure folder exists
os.makedirs("data", exist_ok=True)

# Initialize files
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "sensor1", "sensor2", "sensor3", "date"])

if not os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, "w") as f:
        json.dump({"receive": True, "last_seen": ""}, f)


# ---------- HOME ----------
@app.route("/")
def index():
    return render_template("index.html")


# ---------- RECEIVE SENSOR DATA ----------
@app.route("/api/data", methods=["GET"])
def receive_data():
    s1 = request.args.get("s1")
    s2 = request.args.get("s2")
    s3 = request.args.get("s3")

    with open(STATUS_FILE, "r") as f:
        status = json.load(f)

    if not status["receive"]:
        return "Receiving Stopped", 403

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Read last ID
    last_id = 0
    with open(DATA_FILE, "r") as f:
        rows = list(csv.reader(f))
        if len(rows) > 1:
            last_id = int(rows[-1][0])

    new_id = last_id + 1

    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([new_id, s1, s2, s3, now])

    # Update last seen
    status["last_seen"] = now
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f)

    return "OK"


# ---------- GET ALL DATA ----------
@app.route("/api/all")
def get_all():
    with open(DATA_FILE, "r") as f:
        data = list(csv.DictReader(f))
    return jsonify(data)


# ---------- SEARCH BY DATE ----------
@app.route("/api/search")
def search():
    start = request.args.get("start")
    end = request.args.get("end")

    result = []

    with open(DATA_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_date = datetime.strptime(row["date"], "%Y-%m-%d %H:%M:%S")

            if start and end:
                start_d = datetime.strptime(start, "%Y-%m-%d")
                end_d = datetime.strptime(end, "%Y-%m-%d")

                if start_d <= row_date <= end_d:
                    result.append(row)

    return jsonify(result)


# ---------- START / STOP ----------
@app.route("/api/control")
def control():
    action = request.args.get("action")

    with open(STATUS_FILE, "r") as f:
        status = json.load(f)

    if action == "start":
        status["receive"] = True
    elif action == "stop":
        status["receive"] = False

    with open(STATUS_FILE, "w") as f:
        json.dump(status, f)

    return jsonify(status)


# ---------- STATUS ----------
@app.route("/api/status")
def get_status():
    with open(STATUS_FILE, "r") as f:
        status = json.load(f)

    last_seen = status.get("last_seen", "")

    connected = False
    if last_seen:
        diff = (datetime.now() - datetime.strptime(last_seen, "%Y-%m-%d %H:%M:%S")).seconds
        if diff < 60:
            connected = True

    return jsonify({
        "receiving": status["receive"],
        "esp_status": "Connected" if connected else "Disconnected",
        "last_seen": last_seen
    })


if __name__ == "__main__":
    app.run(debug=True)
