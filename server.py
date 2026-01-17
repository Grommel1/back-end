import os
from flask import Flask, jsonify
import requests

API_KEY = os.environ.get("CLASH_API_KEY")
CLAN_TAG = "#GU88RCLP"

app = Flask(__name__)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

@app.route("/clan")
def clan():
    url = f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG[1:]}/members"
    r = requests.get(url, headers=HEADERS)

    data = r.json()

    # Wenn Supercell einen Fehler zurückgibt
    if "items" not in data:
        return jsonify({
            "error": "Clash Royale API error",
            "status_code": r.status_code,
            "response": data
        }), r.status_code

    return jsonify(data["items"])






