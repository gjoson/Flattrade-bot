import csv
import json
import requests
import websocket
import threading
import time

CLIENT_ID = "FZ37970"
TOKEN = open("token.txt").read().strip()

MASTER_FILE = "Nfo_Index_Derivatives.csv"

QUOTE_URL = "https://piconnect.flattrade.in/PiConnectAPI/GetQuotes"
WS_URL = "wss://piconnect.flattrade.in/PiConnectWSAPI/"

symbol_dict = {}
strike_map = {}
option_chain = {}
token_map = {}

# ------------------------------------------------
# Load contract master and build dictionaries
# ------------------------------------------------

def load_contract_master():

    expiry_selected = None

    with open(MASTER_FILE) as f:

        reader = csv.DictReader(f)

        for row in reader:

            symbol = row["Tradingsymbol"]
            token = row["Token"]
            underlying = row["Symbol"]
            expiry = row["Expiry"]
            strike = row["Strike"]
            opttype = row["Optiontype"]

            symbol_dict[symbol] = token

            if underlying == "NIFTY" and opttype in ("CE","PE"):

                if expiry_selected is None:
                    expiry_selected = expiry

                if expiry != expiry_selected:
                    continue

                strike = int(float(strike))

                if strike not in strike_map:
                    strike_map[strike] = {"CE":None,"PE":None}

                strike_map[strike][opttype] = token

    print("Loaded strikes:", len(strike_map))


# ------------------------------------------------
# Get NIFTY price
# ------------------------------------------------

def get_nifty_price():

    jdata = {
        "uid": CLIENT_ID,
        "exch": "NSE",
        "token": "26000"
    }

    body = f"jData={json.dumps(jdata,separators=(',',':'))}&jKey={TOKEN}"

    r = requests.post(
        QUOTE_URL,
        data=body,
        headers={"Content-Type":"application/x-www-form-urlencoded"}
    )

    data = r.json()

    return float(data["lp"])


# ------------------------------------------------
# Select ATM ±10 strikes
# ------------------------------------------------

def select_strikes():

    price = get_nifty_price()

    atm = round(price/50)*50

    print("NIFTY:", price)
    print("ATM:", atm)

    strikes = []

    for i in range(-10,11):
        strikes.append(atm + i*50)

    tokens = []

    for strike in strikes:

        if strike not in strike_map:
            continue

        ce_token = strike_map[strike]["CE"]
        pe_token = strike_map[strike]["PE"]

        option_chain[strike] = {
            "CE":{"token":ce_token,"ltp":0,"oi":0},
            "PE":{"token":pe_token,"ltp":0,"oi":0}
        }

        token_map[ce_token] = (strike,"CE")
        token_map[pe_token] = (strike,"PE")

        tokens.append(ce_token)
        tokens.append(pe_token)

    return tokens


# ------------------------------------------------
# WebSocket handlers
# ------------------------------------------------

def on_open(ws):

    auth = {
        "t":"a",
        "uid":CLIENT_ID,
        "actid":CLIENT_ID,
        "source":"API",
        "accesstoken":TOKEN
    }

    ws.send(json.dumps(auth))

    print("WebSocket authenticated")


def subscribe(ws,tokens):

    time.sleep(2)

    token_string = "#".join([f"NFO|{t}" for t in tokens])

    sub = {
        "t":"t",
        "k":token_string
    }

    ws.send(json.dumps(sub))

    print("Subscribed tokens:", len(tokens))


def on_message(ws,message):

    data = json.loads(message)

    if "tk" not in data:
        return

    token = data["tk"]

    if token not in token_map:
        return

    strike,opt = token_map[token]

    if "lp" in data:
        option_chain[strike][opt]["ltp"] = float(data["lp"])

    if "oi" in data:
        option_chain[strike][opt]["oi"] = int(data["oi"])


# ------------------------------------------------
# Print option chain
# ------------------------------------------------

def print_chain():

    while True:

        print("\nStrike   CE_LTP   CE_OI   PE_LTP   PE_OI")

        for strike in sorted(option_chain):

            ce = option_chain[strike]["CE"]
            pe = option_chain[strike]["PE"]

            print(
                strike,
                ce["ltp"],
                ce["oi"],
                pe["ltp"],
                pe["oi"]
            )

        time.sleep(3)


# ------------------------------------------------
# MAIN
# ------------------------------------------------

load_contract_master()

tokens = select_strikes()

ws = websocket.WebSocketApp(
    WS_URL,
    on_open=on_open,
    on_message=on_message
)

threading.Thread(target=subscribe,args=(ws,tokens)).start()

threading.Thread(target=print_chain).start()

ws.run_forever()
