import requests
import json
import time
import math
from datetime import datetime

CLIENT_ID = "FZ37970"
TOKEN = open("token.txt").read().strip()

URL = "https://piconnect.flattrade.in/PiConnectAPI/GetOptionChain"

RISK_FREE = 0.06

# ---------- Normal distribution ----------

def N(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def N_prime(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

# ---------- Black76 pricing ----------

def black76_price(F, K, T, sigma, r, call=True):

    if sigma <= 0:
        return 0

    d1 = (math.log(F/K) + 0.5*sigma*sigma*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)

    if call:
        return math.exp(-r*T) * (F*N(d1) - K*N(d2))
    else:
        return math.exp(-r*T) * (K*N(-d2) - F*N(-d1))


# ---------- Implied volatility ----------

def implied_vol(price, F, K, T, r, call=True):

    sigma = 0.2

    for _ in range(20):

        d1 = (math.log(F/K) + 0.5*sigma*sigma*T) / (sigma*math.sqrt(T))

        price_est = black76_price(F,K,T,sigma,r,call)

        vega = F * math.exp(-r*T) * N_prime(d1) * math.sqrt(T)

        if vega == 0:
            return None

        sigma = sigma - (price_est - price) / vega

        if abs(price_est - price) < 0.0001:
            return sigma

    return sigma


# ---------- Greeks ----------

def greeks(F, K, T, sigma, r):

    d1 = (math.log(F/K) + 0.5*sigma*sigma*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)

    delta = math.exp(-r*T) * N(d1)
    gamma = math.exp(-r*T) * N_prime(d1) / (F*sigma*math.sqrt(T))
    vega = F * math.exp(-r*T) * N_prime(d1) * math.sqrt(T)
    theta = -(F*sigma*math.exp(-r*T)*N_prime(d1))/(2*math.sqrt(T))

    return delta,gamma,vega,theta


# ---------- Time to expiry ----------

def time_to_expiry(expiry):

    expiry_dt = datetime.strptime(expiry,"%d-%b-%Y")

    now = datetime.now()

    T = (expiry_dt-now).total_seconds()/(365*24*3600)

    return max(T,0.0001)


# ---------- Main loop ----------

jdata = {
    "uid": CLIENT_ID,
    "exch": "NFO",
    "symbol": "NIFTY"
}

while True:

    body = f"jData={json.dumps(jdata)}&jKey={TOKEN}"

    r = requests.post(
        URL,
        data=body,
        headers={"Content-Type":"application/x-www-form-urlencoded"}
    )

    data = r.json()

    if "values" not in data:
        print("No data from API")
        time.sleep(3)
        continue

    nifty = float(data["spot"])

    atm = round(nifty/50)*50

    expiry = data["expiry"]

    T = time_to_expiry(expiry)

    print("\nNIFTY:",nifty,"ATM:",atm)
    print("Strike  CE_LTP  CE_IV  CE_DELTA  PE_LTP  PE_IV  PE_DELTA")

    for row in data["values"]:

        strike = float(row["strike"])

        if abs(strike-atm) > 500:
            continue

        ce_ltp = row["call_ltp"]
        pe_ltp = row["put_ltp"]

        ce_iv = None
        pe_iv = None
        ce_delta = None
        pe_delta = None

        if ce_ltp:

            ce_iv = implied_vol(ce_ltp,nifty,strike,T,RISK_FREE,True)

            if ce_iv:
                ce_delta,_,_,_ = greeks(nifty,strike,T,ce_iv,RISK_FREE)

        if pe_ltp:

            pe_iv = implied_vol(pe_ltp,nifty,strike,T,RISK_FREE,False)

            if pe_iv:
                pe_delta,_,_,_ = greeks(nifty,strike,T,pe_iv,RISK_FREE)

        print(
            int(strike),
            ce_ltp,
            round(ce_iv,3) if ce_iv else None,
            round(ce_delta,3) if ce_delta else None,
            pe_ltp,
            round(pe_iv,3) if pe_iv else None,
            round(pe_delta,3) if pe_delta else None
        )

    time.sleep(3)