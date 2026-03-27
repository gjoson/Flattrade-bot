import requests
import json
import time
import websocket
import threading

CLIENT_ID = "FZ37970"
TOKEN = open("token.txt").read().strip()

QUOTE_URL = "https://piconnect.flattrade.in/PiConnectAPI/GetQuotes"
CHAIN_URL = "https://piconnect.flattrade.in/PiConnectAPI/GetOptionChain"

HEADERS = {"Content-Type":"application/x-www-form-urlencoded"}

WS_URL = "wss://piconnect.flattrade.in/PiConnectWSAPI/"

# -------------------------
# Get NIFTY price
# -------------------------

def get_nifty():

    jdata = {
        "uid": CLIENT_ID,
        "exch": "NSE",
        "token": "26000"
    }

    body = f"jData={json.dumps(jdata)}&jKey={TOKEN}"

    r = requests.post(QUOTE_URL,data=body,headers=HEADERS)

    data = r.json()

    return float(data["lp"])


# -------------------------
# Get option chain tokens
# -------------------------

def get_chain_tokens(atm):

    jdata = {
        "uid": CLIENT_ID,
        "exch": "NFO",
        "tsym": "NIFTY",
        "strprc": str(atm),
        "cnt": "10"
    }

    body = f"jData={json.dumps(jdata)}&jKey={TOKEN}"

    r = requests.post(CHAIN_URL,data=body,headers=HEADERS)

    data = r.json()

    tokens = []

    for row in data["values"]:
        tokens.append("NFO|" + row["token"])

    return tokens


# -------------------------
# Heartbeat
# -------------------------

def heartbeat(ws):

    while True:

        time.sleep(30)

        ping = {
            "t": "h"
        }

        ws.send(json.dumps(ping))


# -------------------------
# WebSocket callbacks
# -------------------------

def on_open(ws):

    print("WebSocket Connected")

    login = {
        "t": "c",
        "uid": CLIENT_ID,
        "actid": CLIENT_ID,
        "accesstoken": TOKEN
    }

    ws.send(json.dumps(login))


def on_message(ws,message):

    data = json.loads(message)

    if data.get("t") == "ck":

        print("Login success")

        tokens = get_chain_tokens(ATM)

        sub = {
            "t":"t",
            "k":"#".join(tokens)
        }

        ws.send(json.dumps(sub))

        print("Subscribed:",len(tokens),"tokens")

        threading.Thread(target=heartbeat,args=(ws,),daemon=True).start()


    if data.get("lp"):

        strike = data.get("strprc")
        ltp = data.get("lp")
        iv = data.get("iv")
        delta = data.get("delta")

        print(strike,ltp,iv,delta)


def on_error(ws,error):

    print("WS ERROR:",error)


def on_close(ws,a,b):

    print("WebSocket Closed")


# -------------------------
# MAIN
# -------------------------

nifty = get_nifty()

ATM = round(nifty/50)*50

print("NIFTY:",nifty,"ATM:",ATM)

ws = websocket.WebSocketApp(
    WS_URL,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()