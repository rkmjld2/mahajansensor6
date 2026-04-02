from flask import Flask, request, jsonify, render_template
import os
import csv
from datetime import datetime

app = Flask(__name__)

FILE = "data.csv"
API_KEY = "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5"

# ✅ Ensure file exists with header
def create_file():
    if not os.path.exists(FILE):
        with open(FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id","sensor1","sensor2","sensor3","Date"])

create_file()


# -------- INIT FILE --------
if not os.path.exists(FILE):
    with open(FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id","sensor1","sensor2","sensor3","Date"])


# -------- SAVE DATA (FROM ESP) --------
@app.route("/api/data")
def save_data():

    # 🔐 SECURITY CHECK
    if request.args.get("key") != API_KEY:
        return "Unauthorized"

    s1 = request.args.get("s1")
    s2 = request.args.get("s2")
    s3 = request.args.get("s3")

    # DATE FORMAT (same as your requirement)
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # GET LAST ID
    with open(FILE, "r") as f:
        rows = list(csv.reader(f))
        last_id = int(rows[-1][0]) if len(rows) > 1 else 0

    new_id = last_id + 1

    # SAVE
    with open(FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([new_id, s1, s2, s3, now])

    return "Saved"


# -------- GET DATA --------
@app.route("/data")
def get_data():

    with open(FILE, "r") as f:
        reader = csv.DictReader(f)
        data = list(reader)[-50:]

    return jsonify(data)


# -------- SEARCH BY DATE --------
@app.route("/search", methods=["POST"])
def search():

    start = request.form.get("start")
    end = request.form.get("end")

    start_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M")
    end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M")

    result = []

    with open(FILE, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            row_time = datetime.strptime(row["Date"], "%d/%m/%Y %H:%M:%S")

            if start_dt <= row_time <= end_dt:
                result.append(row)

    return jsonify(result)


# -------- DOWNLOAD --------
@app.route("/download", methods=["POST"])
def download():

    start = request.form.get("start")
    end = request.form.get("end")

    start_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M")
    end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M")

    from io import StringIO
    si = StringIO()
    writer = csv.writer(si)

    writer.writerow(["id","sensor1","sensor2","sensor3","Date"])

    with open(FILE, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            row_time = datetime.strptime(row["Date"], "%d/%m/%Y %H:%M:%S")

            if start_dt <= row_time <= end_dt:
                writer.writerow([
                    row["id"],
                    row["sensor1"],
                    row["sensor2"],
                    row["sensor3"],
                    row["Date"]
                ])

    return si.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=data.csv'
    }


# -------- HOME --------
@app.route("/")
def home():
    return render_template("index.html")

#------delete all
@app.route("/delete_all", methods=["GET"])
def delete_all():
    key = request.args.get("key")

    if key != API_KEY:
        return "Unauthorized", 403

    # Keep header, delete all records
    with open(FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id","sensor1","sensor2","sensor3","Date"])

    return "All data deleted successfully"

#...........delete id

@app.route("/delete_id", methods=["GET"])
def delete_by_id():
    key = request.args.get("key")
    delete_id = request.args.get("id")

    if key != API_KEY:
        return "Unauthorized", 403

    if not delete_id:
        return "ID required"

    rows = []

    with open(FILE, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if row[0] != delete_id:
                rows.append(row)

    with open(FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    return f"Record with ID {delete_id} deleted"
	




# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)