from flask import Flask, request, jsonify, render_template, send_file
import os, csv, json
from datetime import datetime
import io

app = Flask(__name__)

DATA_FILE = "data/sensor_data.csv"
STATUS_FILE = "data/status.json"

os.makedirs("data", exist_ok=True)

# Init files
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        csv.writer(f).writerow(["id","sensor1","sensor2","sensor3","date"])

if not os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, "w") as f:
        json.dump({"receive": True, "last_seen": ""}, f)


# ---------- RECEIVE ----------
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

    rows = list(csv.reader(open(DATA_FILE)))
    last_id = int(rows[-1][0]) if len(rows)>1 else 0
    new_id = last_id + 1

    with open(DATA_FILE, "a", newline="") as f:
        csv.writer(f).writerow([new_id,s1,s2,s3,now])

    status["last_seen"] = now
    with open(STATUS_FILE,"w") as f:
        json.dump(status,f)

    return "OK"


# ---------- STATUS ----------
@app.route("/api/status")
def status():
    with open(STATUS_FILE) as f:
        s = json.load(f)

    connected = False
    if s["last_seen"]:
        diff = (datetime.now() - datetime.strptime(s["last_seen"], "%Y-%m-%d %H:%M:%S")).seconds
        connected = diff < 30   # FIXED logic

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

    with open(STATUS_FILE,"w") as f:
        json.dump(s,f)

    return jsonify(s)


# ---------- GET ALL ----------
@app.route("/api/all")
def all_data():
    return jsonify(list(csv.DictReader(open(DATA_FILE))))


# ---------- SQL-LIKE QUERY ----------
@app.route("/api/query", methods=["POST"])
def query():
    q = request.json.get("query","").lower()
    rows = list(csv.DictReader(open(DATA_FILE)))

    # SELECT *
    if "select" in q:
        return jsonify(rows)

    # DELETE id
    if "delete" in q and "id" in q:
        id_val = q.split("id=")[1]
        rows = [r for r in rows if r["id"] != id_val]

    # DELETE date range
    if "delete" in q and "between" in q:
        parts = q.split("between")[1].split("and")
        start = parts[0].strip()
        end = parts[1].strip()

        def keep(r):
            d = datetime.strptime(r["date"], "%Y-%m-%d %H:%M:%S")
            return not (start <= d.strftime("%Y-%m-%d") <= end)

        rows = [r for r in rows if keep(r)]

    # rewrite file
    with open(DATA_FILE,"w",newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id","sensor1","sensor2","sensor3","date"])
        writer.writeheader()
        writer.writerows(rows)

    return jsonify(rows)


# ---------- SEARCH ----------
@app.route("/api/search")
def search():
    start = request.args.get("start")
    end = request.args.get("end")

    result = []

    for r in csv.DictReader(open(DATA_FILE)):
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

    for r in csv.DictReader(open(DATA_FILE)):
        d = datetime.strptime(r["date"], "%Y-%m-%d %H:%M:%S")
        if start <= d.strftime("%Y-%m-%d") <= end:
            writer.writerow([r["id"],r["sensor1"],r["sensor2"],r["sensor3"],r["date"]])

    output.seek(0)

    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name="data.csv")


@app.route("/")
def home():
    return render_template("index.html")
