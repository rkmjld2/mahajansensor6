from flask import Flask, request, jsonify, render_template
import csv, os
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "sensor_data.csv"

# ---------- STATUS ----------
last_seen = None

# ---------- INIT ----------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id","sensor1","sensor2","sensor3","date"])


# ---------- RECEIVE ----------
@app.route("/api/data")
def receive():

    global last_seen
    last_seen = datetime.now()   # ✅ update status

    new_id = request.args.get("id")
    s1 = request.args.get("s1")
    s2 = request.args.get("s2")
    s3 = request.args.get("s3")
    now = request.args.get("time")

    rows = []

    with open(DATA_FILE, "r") as f:
        rows = list(csv.DictReader(f))

    # ✅ DUPLICATE CHECK
    for r in rows:
        if r["id"] == new_id:
            return "DUPLICATE"

    # ✅ SAVE DATA
    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([new_id, s1, s2, s3, now])

    return "OK"


# ---------- STATUS ----------
@app.route("/api/status")
def status():

    global last_seen

    try:
        if last_seen is None:
            return jsonify({"status": "DISCONNECTED"})

        diff = (datetime.now() - last_seen).total_seconds()

        if diff < 15:
            return jsonify({"status": "CONNECTED"})
        else:
            return jsonify({"status": "DISCONNECTED"})
    except:
        return jsonify({"status": "ERROR"})


# ---------- ALL DATA ----------
@app.route("/api/all")
def all_data():
    with open(DATA_FILE, "r") as f:
        return jsonify(list(csv.DictReader(f)))


# ---------- SEARCH ----------
@app.route("/api/search")
def search():

    start = request.args.get("start")
    end = request.args.get("end")

    result = []

    with open(DATA_FILE, "r") as f:
        rows = list(csv.DictReader(f))

        for r in rows:
            if start <= r["date"] <= end:
                result.append(r)

    return jsonify(result)


# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
