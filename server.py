import os
import json
from flask import Flask, jsonify, request
import requests
from datetime import datetime, timezone, timedelta

# =====================
# CONFIG
# =====================
API_KEY = os.environ.get("CLASH_API_KEY")
CLAN_TAG = "#GU88RCLP"  # z.B. #ABCD123

EXCUSES_FILE = "excuses.json"

app = Flask(__name__)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

# =====================
# HILFSFUNKTIONEN
# =====================
def load_excuses():
    if not os.path.exists(EXCUSES_FILE):
        return {}
    with open(EXCUSES_FILE, "r") as f:
        return json.load(f)

def save_excuses(data):
    with open(EXCUSES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_clan_members():
    url = f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG[1:]}/members"
    r = requests.get(url, headers=HEADERS)
    return r.status_code, r.json()

# =====================
# ROUTES
# =====================

@app.route("/")
def home():
    return "Clan Manager Backend läuft ✅"

# ---------------------
# RAW CLAN DATA
# ---------------------
@app.route("/clan")
def clan():
    status, data = get_clan_members()
    return jsonify(data), status

# ---------------------
# AUFBEREITETE SPIELER
# ---------------------
@app.route("/players")
def players():
    status, data = get_clan_members()
    if "items" not in data:
        return jsonify(data), status

    excuses = load_excuses()
    now = datetime.now(timezone.utc)
    result = []

    for p in data["items"]:
        last_seen = datetime.strptime(p["lastSeen"], "%Y%m%dT%H%M%S.%fZ")
        last_seen = last_seen.replace(tzinfo=timezone.utc)
        inactive_days = (now - last_seen).days

        tag = p["tag"]
        excuse = excuses.get(tag)

        is_excused = False
        if excuse:
            until = datetime.fromisoformat(excuse["until"])
            if until > now:
                is_excused = True
            else:
                excuses.pop(tag)
                save_excuses(excuses)

        if is_excused:
            status_text = "excused"
        elif inactive_days >= 3:
            status_text = "danger"
        elif inactive_days >= 2:
            status_text = "warning"
        else:
            status_text = "active"

        result.append({
            "name": p["name"],
            "tag": tag,
            "role": p["role"],
            "trophies": p["trophies"],
            "donations": p["donations"],
            "inactiveDays": inactive_days,
            "status": status_text
        })

    return jsonify(result)

# ---------------------
# SPIELER ENTSCHULDIGEN
# ---------------------
@app.route("/excuse", methods=["POST"])
def excuse_player():
    data = request.json
    tag = data.get("tag")
    days = int(data.get("days", 1))

    excuses = load_excuses()
    until = datetime.now(timezone.utc) + timedelta(days=days)

    excuses[tag] = {
        "until": until.isoformat()
    }

    save_excuses(excuses)
    return jsonify({"ok": True, "tag": tag, "until": until.isoformat()})

# ---------------------
# STATISTIKEN
# ---------------------
@app.route("/stats")
def stats():
    status, data = get_clan_members()
    if "items" not in data:
        return jsonify(data), status

    members = data["items"]

    top_donations = sorted(members, key=lambda x: x["donations"], reverse=True)[:5]
    top_trophies = sorted(members, key=lambda x: x["trophies"], reverse=True)[:5]

    return jsonify({
        "topDonations": [
            {"name": p["name"], "donations": p["donations"]}
            for p in top_donations
        ],
        "topTrophies": [
            {"name": p["name"], "trophies": p["trophies"]}
            for p in top_trophies
        ]
    })

# =====================
if __name__ == "__main__":
    app.run()
