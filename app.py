from flask import Flask, request, jsonify, render_template
import csv, os, time

app = Flask(__name__)

DATA_FILE = "sensor_data.csv"
API_KEY = "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5"

last_seen = 0
collect_data = True

# INIT FILE
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id","sensor1","sensor2","sensor3","time"])


# RECEIVE DATA
@app.route("/api/data")
def receive():
    global last_seen, collect_data

    key = request.args.get("key")
    if key != API_KEY:
        return "Invalid Key", 403

    last_seen = time.time()

    if not collect_data:
        return "Stopped"

    s1 = request.args.get("s1")
    s2 = request.args.get("s2")
    s3 = request.args.get("s3")
    now = request.args.get("time")

    new_id = str(int(time.time()))

    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([new_id, s1, s2, s3, now])

    print("Saved:", s1, s2, s3, now)

    return "OK"


# ALL DATA
@app.route("/api/all")
def all_data():
    with open(DATA_FILE, "r") as f:
        return jsonify(list(csv.DictReader(f)))


# STATUS
@app.route("/status")
def status():
    if time.time() - last_seen < 15:
        return jsonify({"status": "Connected"})
    else:
        return jsonify({"status": "Disconnected"})


# START/STOP
@app.route("/start")
def start():
    global collect_data
    collect_data = True
    return "Started"

@app.route("/stop")
def stop():
    global collect_data
    collect_data = False
    return "Stopped"


# HOME
@app.route("/")
def home():
    return render_template("index.html")


# RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
