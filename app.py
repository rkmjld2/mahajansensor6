from flask import Flask, request, jsonify, render_template, send_file
import os, csv, json, io
from datetime import datetime

app = Flask(__name__)

# ---------- PATH SETUP (VERY IMPORTANT FIX) ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

DATA_FILE = os.path.join(DATA_DIR, "sensor_data.csv")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ---------- INIT FILES ----------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "sensor1", "sensor2", "sensor3", "date"])

if not os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, "w") as f:
        json.dump({"receive": True, "last_seen": ""}, f)


# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- RECEIVE DATA FROM ESP ----------
@app.route("/api/data")
def receive():

    with open(STATUS_FILE) as f:
        status = json.load(f)

    if not status["receive"]:
        return "STOPPED", 403

    s1 = request.args.get("s1")
    s2 = request.args.get("s2")
    s3 = request.args.get("s3")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # read last ID safely
    with open(DATA_FILE, "r") as f:
        rows = list(csv.reader(f))

    last_id = int(rows[-1][0]) if len(rows) > 1 else 0
    new_id = last_id + 1

    # write data
    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([new_id, s1, s2, s3, now])

    # update status
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


# ---------- STATUS ----------
@app.route("/api/status")
def get_status():

    with open(STATUS_FILE) as f:
        s = json.load(f)

    connected = False
    if s["last_seen"]:
        diff = (datetime.now() - datetime.strptime(s["last_seen"], "%Y-%m-%d %H:%M:%S")).seconds
        connected = diff < 30

    return jsonify({
        "receiving": s["receive"],
        "esp_connected": connected,
        "last_seen": s["last_seen"]
    })


# ---------- CONTROL ----------
@app.route("/api/control")
def control():

    action = request.args.get("action")

    with open(STATUS_FILE) as f:
        s = json.load(f)

    if action == "start":
        s["receive"] = True
    elif action == "stop":
        s["receive"] = False

    with open(STATUS_FILE, "w") as f:
        json.dump(s, f)

    return jsonify(s)


# ---------- SEARCH ----------
@app.route("/api/search")
def search():

    start = request.args.get("start")
    end = request.args.get("end")

    result = []

    with open(DATA_FILE, "r") as f:
        for r in csv.DictReader(f):
            d = datetime.strptime(r["date"], "%Y-%m-%d %H:%M:%S")

            if start and end:
                if start <= d.strftime("%Y-%m-%d") <= end:
                    result.append(r)

    return jsonify(result)


# ---------- DOWNLOAD ----------
@app.route("/api/download")
def download():

    start = request.args.get("start")
    end = request.args.get("end")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id","sensor1","sensor2","sensor3","date"])

    with open(DATA_FILE, "r") as f:
        for r in csv.DictReader(f):
            d = datetime.strptime(r["date"], "%Y-%m-%d %H:%M:%S")

            if start <= d.strftime("%Y-%m-%d") <= end:
                writer.writerow([r["id"], r["sensor1"], r["sensor2"], r["sensor3"], r["date"]])

    output.seek(0)

    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name="sensor_data.csv")


# ---------- QUERY ----------
@app.route("/api/query", methods=["POST"])
def query():

    q = request.json.get("query", "").lower().strip()

    with open(DATA_FILE, "r") as f:
        rows = list(csv.DictReader(f))

    # SELECT ALL
    if q == "select *":
        return jsonify(rows)

    # SELECT DATE RANGE
    elif "select between" in q:
        try:
            parts = q.replace("select between","").split("and")
            start = parts[0].strip()
            end = parts[1].strip()

            result = []
            for r in rows:
                d = datetime.strptime(r["date"], "%Y-%m-%d %H:%M:%S")
                if start <= d.strftime("%Y-%m-%d") <= end:
                    result.append(r)

            return jsonify(result)

        except:
            return "Invalid Query", 400

    # DELETE ID
    elif q.startswith("delete id="):
        val = q.split("=")[1]
        rows = [r for r in rows if r["id"] != val]

    # DELETE DATE RANGE
    elif "delete between" in q:
        try:
            parts = q.replace("delete between","").split("and")
            start = parts[0].strip()
            end = parts[1].strip()

            def keep(r):
                d = datetime.strptime(r["date"], "%Y-%m-%d %H:%M:%S")
                return not (start <= d.strftime("%Y-%m-%d") <= end)

            rows = [r for r in rows if keep(r)]

        except:
            return "Invalid Query", 400

    else:
        return "Unsupported Query", 400

    # rewrite file after delete
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id","sensor1","sensor2","sensor3","date"])
        writer.writeheader()
        writer.writerows(rows)

    return jsonify(rows)


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
