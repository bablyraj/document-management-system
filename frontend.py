from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

@app.route("/assets/<path:path>")
def send_assets(path):
    return send_from_directory('assets', path)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

if __name__ == "__main__":
    app.run(debug=True)
