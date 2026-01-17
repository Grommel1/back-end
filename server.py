import os
import json
from flask import Flask, jsonify, request
import requests
from datetime import datetime, timezone, timedelta

# =====================================================
# KONFIGURATION
# =====================================================
API_KEY = os.environ.get("CLASH_API_KEY")
CLAN_TAG = "#DEINCLANTAG"   # z.B. #ABCD123 (WICHTIG: nur Großbuchstaben + Zahlen)

EXCUSES_FILE = "excuses.json"

app = Flask(__name__)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

# =====================================================
# HILFSFUNKTIONEN
# =====================================================
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

# =====================================================
# ROUTES
# =====================================================

@app.route("/")
def home():
    return "Clan Manager Backend läuft ✅"

# -----------------------------------------------------
# ROHDATEN (DEBUG)
# -----------------------------------------------------
@app.route("/clan")
def clan():
    status, data = get_clan_members()
    return jsonify(data), status

# -----------------------------------------------------
# SPIELER + INAKTIVITÄT + ENTSCHULDIGT
# -----------------------------------------------------
@app.route("/players")
def players():
    status, data = get_clan_members()
    if "items" not in data:
        return jsonify(data), status

    excuses = load_excuses()
    now = datetime.now(timezone.utc)
    result = []

    for p in data["items"]:
        last_seen = datetime.strptime(
            p["lastSeen"], "%Y%m%dT%H%M%S.%fZ"
        ).replace(tzinfo=timezone.utc)

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

# -----------------------------------------------------
# SPIELER ENTSCHULDIGEN
# -----------------------------------------------------
@app.route("/excuse", methods=["POST"])
def excuse_player():
    data = request.json
    tag = data.get("tag")
    days = int(data.get("days", 1))

    excuses = load_excuses()
    until = datetime.now(timezone.utc) + timedelta(days=days)

    excuses[tag] = {"until": until.isoformat()}
    save_excuses(excuses)

    return jsonify({
        "ok": True,
        "tag": tag,
        "until": until.isoformat()
    })

# -----------------------------------------------------
# STATISTIKEN (SPENDEN / TROPHÄEN)
# -----------------------------------------------------
@app.route("/stats")
def stats():
    status, data = get_clan_members()
    if "items" not in data:
        return jsonify(data), status

    members = data["items"]

    return jsonify({
        "topDonations": sorted(
            [{"name": m["name"], "donations": m["donations"]} for m in members],
            key=lambda x: x["donations"],
            reverse=True
        )[:5],
        "topTrophies": sorted(
            [{"name": m["name"], "trophies": m["trophies"]} for m in members],
            key=lambda x: x["trophies"],
            reverse=True
        )[:5]
    })

# -----------------------------------------------------
# CLANKRIEG (KÄMPFE / MEDAILLEN)
# -----------------------------------------------------
@app.route("/war")
def war():
    url = f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG[1:]}/currentwar"
    r = requests.get(url, headers=HEADERS)
    data = r.json()

    if "participants" not in data:
        return jsonify(data), r.status_code

    result = []
    for p in data["participants"]:
        decks = p.get("decksUsed", 0)

        result.append({
            "name": p["name"],
            "tag": p["tag"],
            "medals": p.get("fame", 0),
            "decksUsed": decks,
            "decksUsedToday": p.get("decksUsedToday", 0),
            "status": (
                "good" if decks >= 4 else
                "warning" if decks >= 1 else
                "danger"
            )
        })

    return jsonify(result)

# -----------------------------------------------------
# CLANREISE / RIVER RACE
# -----------------------------------------------------
@app.route("/river")
def river():
    url = f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG[1:]}/currentriverrace"
    r = requests.get(url, headers=HEADERS)
    data = r.json()

    if "clans" not in data:
        return jsonify(data), r.status_code

    clan = next(c for c in data["clans"] if c["tag"] == CLAN_TAG)
    result = []

    for p in clan["participants"]:
        fame = p.get("fame", 0)

        result.append({
            "name": p["name"],
            "tag": p["tag"],
            "fame": fame,
            "status": (
                "good" if fame >= 900 else
                "warning" if fame >= 400 else
                "danger"
            )
        })

    return jsonify(result)

# -----------------------------------------------------
# GESAMT-RANKING
# -----------------------------------------------------
@app.route("/leaderboard")
def leaderboard():
    members = requests.get(
        f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG[1:]}/members",
        headers=HEADERS
    ).json().get("items", [])

    war = requests.get(
        f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG[1:]}/currentwar",
        headers=HEADERS
    ).json().get("participants", [])

    river = requests.get(
        f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG[1:]}/currentriverrace",
        headers=HEADERS
    ).json()

    war_map = {p["tag"]: p.get("fame", 0) for p in war}

    river_clan = next(
        (c for c in river.get("clans", []) if c["tag"] == CLAN_TAG),
        None
    )
    river_map = {
        p["tag"]: p.get("fame", 0)
        for p in (river_clan["participants"] if river_clan else [])
    }

    leaderboard = []
    for m in members:
        tag = m["tag"]
        leaderboard.append({
            "name": m["name"],
            "tag": tag,
            "donations": m["donations"],
            "warFame": war_map.get(tag, 0),
            "riverFame": river_map.get(tag, 0),
            "score": m["donations"] + war_map.get(tag, 0) + river_map.get(tag, 0)
        })

    leaderboard.sort(key=lambda x: x["score"], reverse=True)
    return jsonify(leaderboard)

# =====================================================
if __name__ == "__main__":
    app.run()
