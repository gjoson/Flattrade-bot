import requests
import json
import time
import websocket
import threading
import csv
from datetime import datetime
DEBUG = False

nifty_spot = None
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

CONTRACT_FILE = "Nfo_Index_Derivatives.csv"


def get_atm_option_symbol(atm):

    rows = []

    with open(CONTRACT_FILE) as f:
        reader = csv.DictReader(f)

        for r in reader:

            if r["Symbol"] != "NIFTY":
                continue

            if r["Optiontype"] != "CE":
                continue

            strike = int(float(r["Strike"]))

            if strike != atm:
                continue

            expiry = datetime.strptime(r["Expiry"], "%d-%b-%Y")

            rows.append((expiry, r))

    rows.sort()

    nearest = rows[0][1]

    return nearest["Tradingsymbol"]

# -----------------------------------
# Get option chain tokens
# -----------------------------------

def get_chain_tokens(atm):
    tsym = get_atm_option_symbol(atm)

    print("Using tsym:", tsym)
    jdata = {
        "uid": CLIENT_ID,
        "exch": "NFO",
        "tsym": tsym,
        "strprc": str(atm),
        "cnt": "10"
    }

    body = f"jData={json.dumps(jdata)}&jKey={TOKEN}"

    r = requests.post(CHAIN_URL,data=body,headers=HEADERS)

    data = r.json()

    if DEBUG:
        print("OptionChain response:")
    print(json.dumps(data, indent=2))

    print("Unique strikes:", len(option_chain))
    
    tokens = []

    for r in data.get("values", []):

       strike = int(float(r["strprc"]))
       opttype = r["optt"]
       token = r["token"]

       if strike not in option_chain:
        option_chain[strike] = {
            "CE_LTP": None,
            "CE_IV": None,
            "CE_DELTA": None,
            "PE_LTP": None,
            "PE_IV": None,
            "PE_DELTA": None
        }

        token_to_strike[token] = (strike, opttype)

        tokens.append("NFO|" + token)

    return tokens


# -----------------------------------
# Print Option Chain
# -----------------------------------

def display_loop():

    while True:

        time.sleep(1)
        
        if DEBUG:
            continue

        print("\033c", end="")   # clear terminal

        print("Strike  CE_LTP  CE_IV  CE_DELTA   PE_LTP  PE_IV  PE_DELTA")

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
    
    if DEBUG:
        print("WS:", message)

    data = json.loads(message)
    
    if data.get("tk") == "26000":
        global nifty_spot
        nifty_spot = float(data["lp"])
        return

    if data.get("t") in ["ak","ck"]:

        print("Login success")

        tokens = get_chain_tokens(ATM)

        if not tokens:
            print("No tokens received")
            return

        tokens.append("NSE|26000")
        sub = {
            "t":"t",
            "k":"#".join(tokens)
        }

        ws.send(json.dumps(sub))

        print("Subscribed:",len(tokens),"tokens")

        threading.Thread(target=heartbeat,args=(ws,),daemon=True).start()

    if data.get("t") == "tk":

        token = data["tk"]
        ltp = float(data["lp"])

        strike, opttype = token_to_strike[token]

        # CALL option
        if opttype == "CE":

             option_chain[strike]["CE_LTP"] = ltp

             iv, d = calculate_greeks(nifty_spot, strike, ltp, expiry, "CE")

        option_chain[strike]["CE_IV"] = iv
        option_chain[strike]["CE_DELTA"] = d


        # PUT option
        if opttype == "PE":

             option_chain[strike]["PE_LTP"] = ltp

             iv, d = calculate_greeks(nifty_spot, strike, ltp, expiry, "PE")

        option_chain[strike]["PE_IV"] = iv
        option_chain[strike]["PE_DELTA"] = d


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

threading.Thread(target=display_loop, daemon=True).start()

ws = websocket.WebSocketApp(
    WS_URL,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()