from flask import Flask, jsonify
import requests

API_KEY = "HIER_DEIN_API_KEY"
CLAN_TAG = "#DEINCLANTAG"

app = Flask(__name__)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

@app.route("/clan")
def clan():
    url = f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG[1:]}/members"
    r = requests.get(url, headers=HEADERS)
    return jsonify(r.json()["items"])

if __name__ == "__main__":
    app.run()
