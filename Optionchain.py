import requests
import json
import time

CLIENT_ID = "FZ37970"
TOKEN = open("token.txt").read().strip()

url = "https://piconnect.flattrade.in/PiConnectAPI/GetOptionChain"

jdata = {
    "uid": CLIENT_ID,
    "exch": "NFO",
    "symbol": "NIFTY"
}

while True:

    body = f"jData={json.dumps(jdata)}&jKey={TOKEN}"

    r = requests.post(
        url,
        data=body,
        headers={"Content-Type":"application/x-www-form-urlencoded"}
    )

    data = r.json()

    for row in data["values"]:

        strike = row["strike"]

        ce_ltp = row["call_ltp"]
        ce_iv = row["call_iv"]
        ce_delta = row["call_delta"]

        pe_ltp = row["put_ltp"]
        pe_iv = row["put_iv"]
        pe_delta = row["put_delta"]

        print(
            strike,
            ce_ltp,
            ce_iv,
            ce_delta,
            pe_ltp,
            pe_iv,
            pe_delta
        )

    time.sleep(3)