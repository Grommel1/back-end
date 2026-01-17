import os, json, requests
from flask import Flask, jsonify, request
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# ==========================
# KONFIG
# ==========================
API_KEY = os.environ.get("CLASH_API_KEY") or "HIER_DEIN_API_KEY"
CLAN_TAG = "#DEINCLANTAG"
CLAN_TAG_URL = "%23" + CLAN_TAG[1:]

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

EXCUSES_FILE = "excuses.json"

# ==========================
# HELFER
# ==========================
def load_excuses():
    if not os.path.exists(EXCUSES_FILE):
        return {}
    return json.load(open(EXCUSES_FILE))

def save_excuses(d):
    json.dump(d, open(EXCUSES_FILE, "w"), indent=2)

def cr(path):
    r = requests.get(f"https://api.clashroyale.com/v1{path}", headers=HEADERS)
    if r.status_code != 200:
        return None
    return r.json()

def now():
    return datetime.now(timezone.utc)

# ==========================
@app.route("/")
def home():
    return "Backend OK"

# ==========================
# PLAYERS
# ==========================
@app.route("/players")
def players():
    data = cr(f"/clans/{CLAN_TAG_URL}/members")
    if not data:
        return jsonify([])

    excuses = load_excuses()
    res = []

    for p in data["items"]:
        last_seen = datetime.strptime(
            p["lastSeen"], "%Y%m%dT%H%M%S.%fZ"
        ).replace(tzinfo=timezone.utc)

        inactive = (now() - last_seen).days
        tag = p["tag"]

        status = "good"
        if tag in excuses and datetime.fromisoformat(excuses[tag]["until"]) > now():
            status = "excused"
        elif inactive >= 3:
            status = "danger"
        elif inactive >= 2:
            status = "warning"

        res.append({
            "name": p["name"],
            "tag": tag,
            "role": p["role"],
            "inactiveDays": inactive,
            "status": status
        })

    return jsonify(res)

# ==========================
# EXCUSE
# ==========================
@app.route("/excuse", methods=["POST"])
def excuse():
    d = request.json
    excuses = load_excuses()
    until = now() + timedelta(days=int(d["days"]))
    excuses[d["tag"]] = {"until": until.isoformat()}
    save_excuses(excuses)
    return jsonify({"ok": True})

# ==========================
# RIVER / WAR
# ==========================
@app.route("/war")
@app.route("/river")
def river():
    data = cr(f"/clans/{CLAN_TAG_URL}/currentriverrace")
    if not data or "clan" not in data:
        return jsonify([])

    res = []
    for p in data["clan"]["participants"]:
        res.append({
            "name": p["name"],
            "tag": p["tag"],
            "decksUsed": p.get("decksUsed", 0),
            "medals": p.get("fame", 0),
            "fame": p.get("fame", 0),
            "status": "danger" if p.get("decksUsed", 0) == 0 else "good"
        })

    return jsonify(res)

# ==========================
# LEADERBOARD
# ==========================
@app.route("/leaderboard")
def leaderboard():
    members = cr(f"/clans/{CLAN_TAG_URL}/members")
    river = cr(f"/clans/{CLAN_TAG_URL}/currentriverrace")

    if not members:
        return jsonify([])

    river_map = {}
    if river and "clan" in river:
        river_map = {
            p["tag"]: p.get("fame", 0)
            for p in river["clan"]["participants"]
        }

    res = []
    for m in members["items"]:
        score = m["donations"] + river_map.get(m["tag"], 0)
        res.append({
            "name": m["name"],
            "score": score
        })

    res.sort(key=lambda x: x["score"], reverse=True)
    return jsonify(res)

# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
