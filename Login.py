from flask import Flask, request
import hashlib
import requests
import subprocess

app = Flask(__name__)

API_KEY = "971a4014f1984f0cbc85afacfd7816a9"
API_SECRET = "2026.b3bb2a8e05ab48099082a75ba8f4319518942c662cb31be2"

@app.route("/flattrade/callback")
def callback():

    code = request.args.get("code")
    client = request.args.get("client")

    print("CODE:", code)
    print("CLIENT:", client)

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

    print("TOKEN RESPONSE:", data)

    global CLIENT_ID, TOKEN

    CLIENT_ID = data["actid"]
    TOKEN = data["accesstoken"]

    with open("session.json","w") as f:
    json.dump({
        "client_id": client_id,
        "token": token
    }, f)

    if data.get("stat") == "Ok":
        token = data["token"]

        # Save token automatically
        with open("token.txt", "w") as f:
            f.write(token)

        print("Token saved to token.txt")

        return "Login success. Token saved."

    # START OPTIONCHAIN BOT
        subprocess.Popen(["python3","Optionchain.py"])

        print("Optionchain bot started")

        return "Login successful. Bot started."

    return "Login failed"
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
