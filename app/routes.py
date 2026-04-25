from app import app
from flask import render_template, request, redirect, url_for, flash
import os

# Home
@app.route("/")
def home():
    return render_template("index.html")


# Upload
@app.route("/upload", methods=["GET", "POST"])
def upload():

    if request.method == "POST":

        file = request.files.get("file")

        if not file or file.filename == "":
            flash("Please select file")
            return redirect(request.url)

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            file.filename
        )

        file.save(filepath)

        flash("File uploaded successfully")

        return redirect(url_for("upload"))

    return render_template("upload.html")


# Dashboard
@app.route("/dashboard")
def dashboard():

    files = os.listdir(app.config["UPLOAD_FOLDER"])

    return render_template(
        "dashboard.html",
        files=files
    )


# Scanner
@app.route("/scanner")
def scanner():
    return render_template("scanner.html")


# Report
@app.route("/report")
def report():
    return render_template("report.html")