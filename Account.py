import requests
import json

LIMITS_URL = "https://piconnect.flattrade.in/PiConnectAPI/Limits"

def get_limits():

    jdata = {
        "uid": CLIENT_ID,
        "actid": CLIENT_ID
    }

    body = f"jData={json.dumps(jdata)}&jKey={TOKEN}"

    r = requests.post(LIMITS_URL, data=body, headers=HEADERS)

    data = r.json()

if __name__ == "__main__":
    get_limits()

    if data.get("stat") != "Ok":
        print("Limits error:", data)
        return

    cash = float(data["cash"])
    margin_used = float(data["marginused"])
    pnl_realized = float(data["rpnl"])
    pnl_unrealized = float(data["urmtom"])

    print("\nACCOUNT STATUS")
    print("----------------")
    print("Cash:", cash)
    print("Margin Used:", margin_used)
    print("Realized PnL:", pnl_realized)
    print("Unrealized PnL:", pnl_unrealized)