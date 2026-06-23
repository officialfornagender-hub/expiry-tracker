from flask import Flask, request, redirect, session
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

app = Flask(__name__)
app.secret_key = "expirytracker123"
# ==========================
# GOOGLE SHEETS
# ==========================

import os
import json
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

service_account_info = json.loads(
    os.environ["GOOGLE_CREDENTIALS"]
)

creds = Credentials.from_service_account_info(
    service_account_info,
    scopes=SCOPES
)

client = gspread.authorize(creds)

sheet = client.open_by_key(
    "1xRafUJUNpwuMQkV3CumAYwIkNn5MdM57o8CtHWMzlK8"
).sheet1


# ==========================
# STATUS UPDATE
# ==========================

def update_statuses():

    records = sheet.get_all_records()

    for i, row in enumerate(records, start=2):

        try:
            doe = str(row["DOE"]).strip()

            try:
                doe_date = datetime.strptime(doe, "%d/%m/%Y")
            except:
                doe_date = datetime.strptime(doe, "%Y-%m-%d")

            days_left = (doe_date.date() - datetime.today().date()).days

            if days_left < 0:
                new_status = "Expired"
            elif days_left <= 30:
                new_status = "Expiring Soon"
            else:
                new_status = "Active"

            if str(row["Status"]) != new_status:
                sheet.update_cell(i, 7, new_status)

        except:
            pass


# ==========================
# LOGIN
# ==========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":

            session["logged_in"] = True
            return redirect("/")

        return """
        <h3 style='color:red'>
        Invalid Username or Password
        </h3>
        <a href='/login'>Try Again</a>
        """

    return """
    <html>
    <head>

    <style>

    body{
        font-family:Arial;
        background:#f4f6f9;
    }

    .login-box{
        width:350px;
        margin:100px auto;
        background:white;
        padding:30px;
        border-radius:15px;
        box-shadow:0 0 15px rgba(0,0,0,.2);
        text-align:center;
    }

    input{
        width:90%;
        padding:10px;
        margin:10px;
    }

    button{
        background:#0078d7;
        color:white;
        border:none;
        padding:10px 20px;
        border-radius:5px;
        cursor:pointer;
    }

    </style>

    </head>

    <body>

    <div class="login-box">

        <h2>🔐 Expiry Tracker Login</h2>

        <form method="POST">

            <input
            type="text"
            name="username"
            placeholder="Username"
            required>

            <input
            type="password"
            name="password"
            placeholder="Password"
            required>

            <button type="submit">
                Login
            </button>

        </form>

    </div>

    </body>
    </html>
    """
# ==========================
# HOME
# ==========================

@app.route("/")
def home():

    if not session.get("logged_in"):
        return redirect("/login")

    update_statuses()

    records = sheet.get_all_records()

    search_text = request.args.get("search", "")

    html = f"""
    <html>
    <head>

    <style>

    body {{
        font-family: Arial;
        background:#f4f6f9;
        padding:20px;
    }}

    .card {{
        background:white;
        padding:20px;
        border-radius:12px;
        box-shadow:0px 2px 10px rgba(0,0,0,.1);
    }}

    .btn {{
        background:#0078d7;
        color:white;
        border:none;
        padding:10px 15px;
        border-radius:6px;
        cursor:pointer;
    }}

    table {{
        width:100%;
        border-collapse:collapse;
        background:white;
    }}

    th {{
        background:#0078d7;
        color:white;
        padding:10px;
    }}

    td {{
        padding:8px;
        text-align:center;
    }}

    tr:nth-child(even) {{
        background:#f7f7f7;
    }}

    input[type=text] {{
        padding:10px;
        width:250px;
    }}

    </style>

    </head>

    <body>

    <div class="card">

    <div style="
background:#003366;
color:white;
padding:20px;
border-radius:10px;
margin-bottom:20px;">

<h1 style="margin:0;">
📦 Centro Expiry Management System
</h1>

<p style="margin-top:5px;">
Track Expiry • Monitor Inventory • Reduce Losses
</p>

</div>

    <a href="/add">
        <button class="btn">➕ Add Product</button>
    </a>

    <a href="/dashboard">
        <button class="btn">📊 Dashboard</button>
    </a>

    <a href="/alerts">
        <button class="btn">⚠ Expiry Alerts</button>
    </a>
<a href="/logout">
    <button class="btn">🚪 Logout</button>
</a>
    <br><br>

    <form method="GET">

        <input
        type="text"
        name="search"
        placeholder="Enter CNO or EAN"
        value="{search_text}">

        <button class="btn">Search</button>

    </form>

    <br>

    <table>

        <tr>
            <th>ID No</th>
            <th>CNO</th>
            <th>EAN</th>
            <th>DOM</th>
            <th>DOE</th>
            <th>Entry Date</th>
            <th>Status</th>
        </tr>
    """

    for row in records:

        if search_text:

            if (
                search_text not in str(row["CNO"])
                and search_text not in str(row["EAN Code"])
            ):
                continue

        color = ""

        if str(row["Status"]) == "Expired":
            color = "#ffcccc"

        elif str(row["Status"]) == "Expiring Soon":
            color = "#fff0b3"

        html += f"""
        <tr bgcolor="{color}">
            <td>{row['ID No']}</td>
            <td>{row['CNO']}</td>
            <td>{row['EAN Code']}</td>
            <td>{row['DOM']}</td>
            <td>{row['DOE']}</td>
            <td>{row['Entry Date']}</td>
            <td>{row['Status']}</td>
        </tr>
        """

    html += """
    </table>

    </div>

    </body>
    </html>
    """

    return html


# ==========================
# ADD PRODUCT
# ==========================

@app.route("/add", methods=["GET", "POST"])
def add_product():

    if request.method == "POST":

        records = sheet.get_all_records()

        next_id = len(records) + 1

        cno = request.form["cno"]
        ean = request.form["ean"]
        dom = request.form["dom"]
        doe = request.form["doe"]

        doe_date = datetime.strptime(doe, "%Y-%m-%d")

        days_left = (doe_date.date() - datetime.today().date()).days

        if days_left < 0:
            status = "Expired"
        elif days_left <= 30:
            status = "Expiring Soon"
        else:
            status = "Active"

        entry_date = datetime.today().strftime("%d-%m-%Y")

        sheet.append_row([
            next_id,
            cno,
            ean,
            dom,
            doe,
            entry_date,
            status
        ])

        return redirect("/")

    return """
<html>
<head>

<style>

body{
    font-family:Arial;
    background:#f4f6f9;
}

.card{
    width:600px;
    margin:30px auto;
    background:white;
    padding:30px;
    border-radius:15px;
    box-shadow:0 0 15px rgba(0,0,0,.15);
}

input{
    width:95%;
    padding:12px;
    margin-top:5px;
    margin-bottom:15px;
    border:1px solid #ccc;
    border-radius:6px;
}

.btn{
    background:#0078d7;
    color:white;
    border:none;
    padding:12px 18px;
    border-radius:6px;
    cursor:pointer;
}

.btn:hover{
    background:#005fb8;
}

</style>

</head>

<body>

<div class="card">

<h1>📦 Add Product</h1>

<form method="POST">

<label>CNO</label><br>
<input type="text" name="cno" required>

<label>EAN Code</label><br>
<input type="text" id="ean" name="ean" required>

<button type="button" class="btn" onclick="startScanner()">
📷 Scan Barcode
</button>

<br><br>

<div id="reader" style="width:300px;"></div>

<br>

<label>DOM</label><br>
<input type="date" id="dom" name="dom">

<button type="button" class="btn" onclick="voiceDOM()">
🎤 Speak DOM
</button>

<br><br>

<label>DOE</label><br>
<input type="date" id="doe" name="doe">

<button type="button" class="btn" onclick="voiceDOE()">
🎤 Speak DOE
</button>

<br><br>

<button class="btn">
💾 Save Product
</button>

</form>

<br>

<a href="/">
<button class="btn">
🏠 Back Home
</button>
</a>

</div>

<script src="https://unpkg.com/html5-qrcode"></script>

<script>

function startScanner(){

    const html5QrCode =
    new Html5Qrcode("reader");

    html5QrCode.start(
        {facingMode:"environment"},
        {fps:10, qrbox:250},

        (decodedText)=>{

            document.getElementById("ean").value =
            decodedText;

            html5QrCode.stop();
        }
    );
}

function convertDate(text){

    const date = new Date(text);

    if(!isNaN(date)){
        return date.toISOString().split('T')[0];
    }

    return "";
}

function voiceDOM(){

    const recognition =
    new webkitSpeechRecognition();

    recognition.lang = "en-IN";

    recognition.start();

    recognition.onresult = function(event){

        let spoken =
        event.results[0][0].transcript;

        document.getElementById("dom").value =
        convertDate(spoken);
    };
}

function voiceDOE(){

    const recognition =
    new webkitSpeechRecognition();

    recognition.lang = "en-IN";

    recognition.start();

    recognition.onresult = function(event){

        let spoken =
        event.results[0][0].transcript;

        document.getElementById("doe").value =
        convertDate(spoken);
    };
}

</script>

</body>
</html>
"""


# ==========================
# DASHBOARD
# ==========================

@app.route("/dashboard")
def dashboard():

    records = sheet.get_all_records()

    total = len(records)

    active = 0
    expiring = 0
    expired = 0

    for row in records:

        status = str(row["Status"])

        if status == "Active":
            active += 1

        elif status == "Expiring Soon":
            expiring += 1

        elif status == "Expired":
            expired += 1

    return f"""
<html>
<head>

<style>

body {{
    font-family:Arial;
    background:#f4f6f9;
    padding:30px;
}}

.header {{
    background:#003366;
    color:white;
    padding:20px;
    border-radius:12px;
    margin-bottom:20px;
}}

.box {{
    width:220px;
    display:inline-block;
    padding:25px;
    margin:10px;
    border-radius:15px;
    color:white;
    text-align:center;
    font-size:24px;
    font-weight:bold;
    box-shadow:0 0 15px rgba(0,0,0,.15);
}}

.total{{background:#0078d7;}}
.active{{background:#28a745;}}
.expiring{{background:#ff9800;}}
.expired{{background:#dc3545;}}

.btn{{
    background:#0078d7;
    color:white;
    border:none;
    padding:12px 18px;
    border-radius:8px;
    cursor:pointer;
    text-decoration:none;
}}

</style>

</head>

<body>

<div class="header">
<h1>📊 Expiry Dashboard</h1>
<p>Real Time Inventory Monitoring</p>
</div>

<div class="box total">
📦<br>Total Products<br>{total}
</div>

<div class="box active">
🟢<br>Active Products<br>{active}
</div>

<div class="box expiring">
🟠<br>Expiring Soon<br>{expiring}
</div>

<div class="box expired">
🔴<br>Expired Products<br>{expired}
</div>

<br><br>

<a href="/" class="btn">
🏠 Back Home
</a>

</body>
</html>
"""


# ==========================
# ALERTS
# ==========================

@app.route("/alerts")
def alerts():

    records = sheet.get_all_records()

    html = """
    <h1>⚠ Expiry Alerts</h1>

    <a href="/">Back</a>

    <br><br>

    <table border="1" cellpadding="8">

    <tr>
        <th>ID</th>
        <th>CNO</th>
        <th>EAN</th>
        <th>DOE</th>
        <th>Status</th>
        <th>Days Left</th>
    </tr>
    """

    today = datetime.today()

    for row in records:

        try:

            doe = str(row["DOE"])

            try:
                doe_date = datetime.strptime(doe,"%d/%m/%Y")
            except:
                doe_date = datetime.strptime(doe,"%Y-%m-%d")

            days_left = (
                doe_date.date() - today.date()
            ).days

            if days_left > 30:
                continue

            color = "#fff0b3"

            if days_left < 0:
                color = "#ffcccc"

            html += f"""
            <tr bgcolor="{color}">
                <td>{row['ID No']}</td>
                <td>{row['CNO']}</td>
                <td>{row['EAN Code']}</td>
                <td>{row['DOE']}</td>
                <td>{row['Status']}</td>
                <td>{days_left}</td>
            </tr>
            """

        except:
            pass

    html += "</table>"

    return html

# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")
if __name__ == "__main__":
    app.run(debug=True)
