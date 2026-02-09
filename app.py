from flask import Flask, render_template, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return render_template("timetable.html")


@app.route('/api/ping')
def api_ping():
    return jsonify({"status": "ok", "message": "backend reachable"})


@app.route('/api/timetable')
def api_timetable():
    # Minimal placeholder JSON. Replace with real data logic.
    sample = {
        "title": "Caleb Timetable",
        "generated": "2026-01-26",
        "levels": ["L1", "L2", "L3", "L4"]
    }
    return jsonify(sample)


@app.route('/api/assistants')
def api_assistants():
    return jsonify({"assistants": []})


@app.route('/api/professors')
def api_professors():
    return jsonify({"professors": []})


@app.route('/api/rooms')
def api_rooms():
    return jsonify({"rooms": []})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
