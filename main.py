from flask import Flask, render_template, request, redirect
import webbrowser
import subprocess
import sys
import os

app = Flask(__name__)

# Allowed commands for safety
ALLOWED_COMMANDS = {
    "open": lambda arg: webbrowser.open(arg),
    "ls": lambda arg="": subprocess.getoutput(f"ls {arg}"),
    "pwd": lambda arg="": subprocess.getoutput("pwd"),
}

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/execute", methods=["POST"])
def execute():
    command_text = request.form.get("command")
    if not command_text:
        return render_template("index.html", result="No command entered!")

    parts = command_text.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ALLOWED_COMMANDS:
        try:
            result = ALLOWED_COMMANDS[cmd](arg)
            return render_template("index.html", result=result or "Command executed successfully!")
        except Exception as e:
            return render_template("index.html", result=f"Error: {e}")
    else:
        return render_template("index.html", result=f"Command '{cmd}' not allowed!")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
