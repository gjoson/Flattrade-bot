import csv
import json
import requests
import websocket
import threading
import time
from datetime import datetime

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
    global strike_map, symbol_dict

    symbol_dict.clear()
    strike_map.clear()

    expiries = set()

    # Pass 1: collect NIFTY expiries
    with open(MASTER_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            underlying = (row.get("Symbol") or "").strip()
            if underlying == "NIFTY":
                expiry = (row.get("Expiry") or "").strip()
                if expiry:
                    expiries.add(expiry)

    if not expiries:
        raise ValueError("No NIFTY expiries found in contract master")

    expiry_dates = []
    for e in expiries:
        try:
            expiry_dates.append(datetime.strptime(e, "%d-%b-%Y"))
        except ValueError:
            pass

    if not expiry_dates:
        raise ValueError("Could not parse any expiry dates from contract master")

    today = datetime.now().date()
    future_expiries = [e for e in expiry_dates if e.date() >= today]

    if not future_expiries:
        raise ValueError("No future NIFTY expiries found")

    nearest_expiry = min(future_expiries)
    nearest_expiry_str = nearest_expiry.strftime("%d-%b-%Y")

    print("Using expiry:", nearest_expiry_str)

    # Pass 2: build symbol_dict and strike_map for nearest expiry only
    with open(MASTER_FILE, newline='') as f:
        reader = csv.DictReader(f)

        for row in reader:
            symbol = (row.get("TradingSymbol") or row.get("Tradingsymbol") or row.get("Symbol") or "").strip()
            token = (row.get("Token") or "").strip()
            underlying = (row.get("Symbol") or "").strip()
            expiry = (row.get("Expiry") or "").strip()
            strike_raw = (row.get("StrikePrice") or row.get("Strike") or "").strip()
            opttype = (row.get("OptionType") or row.get("Optiontype") or "").strip()

            if not symbol or not token:
                continue

            symbol_dict[symbol] = token

            if underlying != "NIFTY":
                continue

            if expiry != nearest_expiry_str:
                continue

            if opttype not in ("CE", "PE"):
                continue

            try:
                strike = int(float(strike_raw))
            except ValueError:
                continue

            if strike not in strike_map:
                strike_map[strike] = {"CE": None, "PE": None}

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

    body = f"jData={json.dumps(jdata, separators=(',', ':'))}&jKey={TOKEN}"

    r = requests.post(
        QUOTE_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    data = r.json()
    return float(data["lp"])


# ------------------------------------------------
# Select ATM ±10 strikes
# ------------------------------------------------

def select_strikes():
    price = get_nifty_price()
    atm = round(price / 50) * 50

    print("NIFTY:", price)
    print("ATM:", atm)

    strikes = []
    for i in range(-10, 11):
        strikes.append(atm + i * 50)

    tokens = []

    for strike in strikes:
        if strike not in strike_map:
            continue

        ce_token = strike_map[strike]["CE"]
        pe_token = strike_map[strike]["PE"]

        if not ce_token or not pe_token:
            continue

        option_chain[strike] = {
            "CE": {"token": ce_token, "ltp": 0, "oi": 0},
            "PE": {"token": pe_token, "ltp": 0, "oi": 0}
        }

        token_map[str(ce_token)] = (strike, "CE")
        token_map[str(pe_token)] = (strike, "PE")

        tokens.append(str(ce_token))
        tokens.append(str(pe_token))

    return tokens


# ------------------------------------------------
# WebSocket handlers
# ------------------------------------------------

def on_open(ws):
    auth = {
        "t": "a",
        "uid": CLIENT_ID,
        "actid": CLIENT_ID,
        "source": "API",
        "accesstoken": TOKEN
    }

    ws.send(json.dumps(auth))
    print("WebSocket authenticated")


def subscribe(ws, tokens):
    time.sleep(2)

    token_string = "#".join([f"NFO|{t}" for t in tokens])

    sub = {
        "t": "t",
        "k": token_string
    }

    ws.send(json.dumps(sub))
    print("Subscribed tokens:", len(tokens))


def on_message(ws, message):
    data = json.loads(message)

    if "tk" not in data:
        return

    token = str(data["tk"])

    if token not in token_map:
        return

    strike, opt = token_map[token]

    if "lp" in data:
        option_chain[strike][opt]["ltp"] = float(data["lp"])

    if "oi" in data:
        option_chain[strike][opt]["oi"] = int(float(data["oi"]))


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

threading.Thread(target=subscribe, args=(ws, tokens), daemon=True).start()
threading.Thread(target=print_chain, daemon=True).start()

ws.run_forever()
