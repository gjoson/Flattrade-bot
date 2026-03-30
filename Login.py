from flask import Flask, request
import hashlib
import requests
import json
import os

API_KEY = "971a4014f1984f0cbc85afacfd7816a9"
API_SECRET = "2026.b3bb2a8e05ab48099082a75ba8f4319518942c662cb31be2"

app = Flask(__name__)


@app.route("/flattrade/callback")
def callback():

    code = request.args.get("code")
    client = request.args.get("client")

    print("Code:", code)
    print("Client:", client)

    raw = API_KEY + code + API_SECRET
    sha256 = hashlib.sha256(raw.encode()).hexdigest()

    payload = {
        "api_key": API_KEY,
        "request_code": code,
        "api_secret": sha256
    }

    r = requests.post(
        "https://authapi.flattrade.in/trade/apitoken",
        json=payload
    )

    data = r.json()

    client = data["actid"]
    token = data["access_token"]
    if os.path.exists("token.txt"):
       os.remove("token.txt")

    with open("token.txt", "w") as f:
       f.write(f"{client}\n{token}")

print("Token saved to token.txt")

    print("Response:", data)

    if data.get("stat") != "Ok":
        return "Login failed"

    session = {
        "client_id": data["actid"],
        "token": data["access_token"]
    }

    with open("session.json", "w") as f:
        json.dump(session, f)

    return "Login successful. Token saved."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)