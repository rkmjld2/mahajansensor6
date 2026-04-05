from flask import Flask, request, jsonify, render_template, send_file
import csv, os, time

app = Flask(__name__)

DATA_FILE = "sensor_data.csv"
API_KEY = "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5"

last_seen = 0
collect_data = True

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id","sensor1","sensor2","sensor3","time"])


@app.route("/api/data")
def receive():
    global last_seen

    key = request.args.get("key")
    if key != API_KEY:
        return "Invalid Key", 403

    last_seen = time.time()

    s1 = request.args.get("s1")
    s2 = request.args.get("s2")
    s3 = request.args.get("s3")
    now = request.args.get("time")

    with open(DATA_FILE, "r") as f:
        rows = list(csv.DictReader(f))

    # duplicate check
    for r in rows:
        if r["time"] == now and r["sensor1"] == s1:
            return "Duplicate"

    new_id = int(rows[-1]["id"]) + 1 if rows else 1

    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([new_id, s1, s2, s3, now])

    return "OK"


@app.route("/api/all")
def all_data():
    with open(DATA_FILE, "r") as f:
        return jsonify(list(csv.DictReader(f)))


@app.route("/download")
def download():
    return send_file(DATA_FILE, as_attachment=True)


@app.route("/status")
def status():
    return jsonify({"status": "Connected" if time.time()-last_seen<15 else "Disconnected"})


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0")
