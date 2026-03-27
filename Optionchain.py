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

option_chain = {}
token_to_strike = {}

# -----------------------------------
# Get NIFTY price
# -----------------------------------

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


# -----------------------------------
# Get option chain tokens
# -----------------------------------

def get_chain_tokens(atm):

    jdata = {
        "uid": CLIENT_ID,
        "exch": "NFO",
        "tsym": "NIFTY",
        "strprc": str(atm),
        "cnt": "10"
    }

    body = f"jData={json.dumps(jdata)}&jKey={TOKEN}

    r = requests.post(CHAIN_URL,data=body,headers=HEADERS)

    data = r.json()

    tokens = []

    if "values" not in data:
        print("Option chain error:",data)
        return tokens

    for row in data["values"]:

        strike = int(row["strprc"])

        ce = row["call_token"]
        pe = row["put_token"]

        option_chain[strike] = {
            "CE_LTP":None,
            "CE_IV":None,
            "CE_DELTA":None,
            "PE_LTP":None,
            "PE_IV":None,
            "PE_DELTA":None
        }

        token_to_strike[ce] = (strike,"CE")
        token_to_strike[pe] = (strike,"PE")

        tokens.append("NFO|" + ce)
        tokens.append("NFO|" + pe)

    return tokens


# -----------------------------------
# Print Option Chain
# -----------------------------------

def print_chain():

    print("\nStrike  CE_LTP  CE_IV  CE_DELTA   PE_LTP  PE_IV  PE_DELTA")

    for strike in sorted(option_chain):

        row = option_chain[strike]

        print(
            strike,
            row["CE_LTP"],
            row["CE_IV"],
            row["CE_DELTA"],
            row["PE_LTP"],
            row["PE_IV"],
            row["PE_DELTA"]
        )


# -----------------------------------
# Heartbeat
# -----------------------------------

def heartbeat(ws):

    while True:

        time.sleep(30)

        ws.send(json.dumps({"t":"h"}))


# -----------------------------------
# WebSocket callbacks
# -----------------------------------

def on_open(ws):

    print("WebSocket Connected")

    login = {
        "t":"a",
        "uid":CLIENT_ID,
        "actid":CLIENT_ID,
        "accesstoken":TOKEN
    }

    ws.send(json.dumps(login))


def on_message(ws,message):

    data = json.loads(message)

    print("WS:",data)

    if data.get("t") in ["ak","ck"]:

        print("Login success")

        tokens = get_chain_tokens(ATM)

        if not tokens:
            print("No tokens received")
            return

        sub = {
            "t":"t",
            "k":"#".join(tokens)
        }

        ws.send(json.dumps(sub))

        print("Subscribed:",len(tokens),"tokens")

        threading.Thread(target=heartbeat,args=(ws,),daemon=True).start()


    if data.get("t") in ["tk","tf"]:

        token = data.get("tk")

        if token not in token_to_strike:
            return

        strike,side = token_to_strike[token]

        if side == "CE":

            option_chain[strike]["CE_LTP"] = data.get("lp")
            option_chain[strike]["CE_IV"] = data.get("iv")
            option_chain[strike]["CE_DELTA"] = data.get("delta")

        else:

            option_chain[strike]["PE_LTP"] = data.get("lp")
            option_chain[strike]["PE_IV"] = data.get("iv")
            option_chain[strike]["PE_DELTA"] = data.get("delta")

        print_chain()


def on_error(ws,error):

    print("WS ERROR:",error)


def on_close(ws,a,b):

    print("WebSocket Closed")


# -----------------------------------
# MAIN
# -----------------------------------

nifty = get_nifty()

ATM = int(round(nifty/50)*50)

print("NIFTY:",nifty,"ATM:",ATM)

ws = websocket.WebSocketApp(
    WS_URL,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()