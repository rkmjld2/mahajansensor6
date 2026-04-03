from flask import Flask, request, jsonify, render_template
import csv, os

app = Flask(__name__)

DATA_FILE = "sensor_data.csv"

# ---------- INIT ----------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id","sensor1","sensor2","sensor3","date"])


# ---------- RECEIVE ----------
@app.route("/api/data")
def receive():

    new_id = request.args.get("id")
    s1 = request.args.get("s1")
    s2 = request.args.get("s2")
    s3 = request.args.get("s3")
    now = request.args.get("time")

    rows = []

    with open(DATA_FILE, "r") as f:
        rows = list(csv.DictReader(f))

    # ✅ CHECK DUPLICATE
    for r in rows:
        if r["id"] == new_id:
            return "DUPLICATE"

    # ✅ ADD NEW
    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([new_id, s1, s2, s3, now])

    return "OK"


# ---------- VIEW ----------
@app.route("/api/all")
def all_data():
    with open(DATA_FILE, "r") as f:
        return jsonify(list(csv.DictReader(f)))


# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
