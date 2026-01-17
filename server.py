from flask import Flask, jsonify
import requests

API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjcyMTExZGUxLWY2ZGQtNDdlNS1iOGFhLTBmYTQyYTk5NjAyNyIsImlhdCI6MTc2ODYxNDkxMCwic3ViIjoiZGV2ZWxvcGVyLzc1YjQzNDAzLWUzYWEtYTdkOC05MzdlLWU2N2FiZDc2NTJlNyIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyI3NC4yMjAuNTEuMCIsIjc0LjIyMC41OS4wIiwiNzQuMjIwLjU5LjI0IiwiNzQuMjIwLjUxLjI0Il0sInR5cGUiOiJjbGllbnQifV19.Z83OoT-T2jGDaGrkdlDBrdPv-96kX5xrB_xR0cqkhFrNLoAoD_SPy5NprUamxYNmER2lcvZSZtGyKUGTVM8BDA"
CLAN_TAG = "FEUERDOCTOR.de"

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

