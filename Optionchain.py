import requests
import json
import time
import csv
from datetime import datetime

CLIENT_ID = "FZ37970"
TOKEN = open("token.txt").read().strip()

QUOTE_URL = "https://piconnect.flattrade.in/PiConnectAPI/GetQuotes"

MASTER_FILE = "Nfo_Index_Derivatives.csv"

# -----------------------------
# load nearest weekly expiry
# -----------------------------

def load_tokens():

    expiries = set()

    with open(MASTER_FILE) as f:

        reader = csv.DictReader(f)

        for row in reader:

            if row["Symbol"] == "NIFTY" and row["Optiontype"] in ("CE","PE"):

                expiry = row["Expiry"]

                expiry_date = datetime.strptime(expiry,"%d-%b-%Y")

                if expiry_date.date() >= datetime.now().date():
                    expiries.add(expiry)

    # convert to datetime for sorting
    expiry_dates = [(datetime.strptime(e,"%d-%b-%Y"),e) for e in expiries]

    nearest_expiry = min(expiry_dates)[1]

    print("Nearest expiry:",nearest_expiry)

    strike_map = {}

    with open(MASTER_FILE) as f:

        reader = csv.DictReader(f)

        for row in reader:

            if row["Symbol"] != "NIFTY":
                continue

            if row["Expiry"] != nearest_expiry:
                continue

            opt = row["Optiontype"]

            if opt not in ("CE","PE"):
                continue

            strike = int(float(row["Strike"]))

            token = row["Token"]

            if strike not in strike_map:
                strike_map[strike] = {}

            strike_map[strike][opt] = token

    return strike_map


# -----------------------------
# get nifty price
# -----------------------------

def get_nifty_price():

    jdata = {
        "uid": CLIENT_ID,
        "exch": "NSE",
        "token": "26000"
    }

    body = f"jData={json.dumps(jdata)}&jKey={TOKEN}"

    r = requests.post(
        QUOTE_URL,
        data=body,
        headers={"Content-Type":"application/x-www-form-urlencoded"}
    )

    data = r.json()

    return float(data["lp"])


# -----------------------------
# get option data
# -----------------------------

def get_option(token):

    jdata = {
        "uid": CLIENT_ID,
        "exch": "NFO",
        "token": token
    }

    body = f"jData={json.dumps(jdata)}&jKey={TOKEN}"

    r = requests.post(
        QUOTE_URL,
        data=body,
        headers={"Content-Type":"application/x-www-form-urlencoded"}
    )

    return r.json()


# -----------------------------
# main
# -----------------------------

strike_map = load_tokens()

while True:

    price = get_nifty_price()

    atm = round(price/50)*50

    print("\nNIFTY:",price,"ATM:",atm)
    print("Strike  CE_LTP  CE_IV  CE_DELTA   PE_LTP  PE_IV  PE_DELTA")

    for i in range(-10,11):

        strike = atm + i*50

        if strike not in strike_map:
            continue

        ce_token = strike_map[strike].get("CE")
        pe_token = strike_map[strike].get("PE")

        ce = get_option(ce_token)
        pe = get_option(pe_token)

        ce_ltp = ce.get("lp")
        ce_iv = ce.get("iv")
        ce_delta = ce.get("delta")

        pe_ltp = pe.get("lp")
        pe_iv = pe.get("iv")
        pe_delta = pe.get("delta")

        print(
            strike,
            ce_ltp,
            ce_iv,
            ce_delta,
            pe_ltp,
            pe_iv,
            pe_delta
        )

    time.sleep(5)