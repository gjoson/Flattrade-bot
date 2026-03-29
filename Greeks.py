import math
from datetime import datetime

# -----------------------------
# Normal CDF
# -----------------------------
def norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


# -----------------------------
# Black76 d1
# -----------------------------
def d1(S, K, r, sigma, T):
    return (math.log(S / K) + (r + sigma * sigma / 2) * T) / (sigma * math.sqrt(T))


# -----------------------------
# Delta
# -----------------------------
def delta(S, K, r, sigma, T, option_type):

    d_1 = d1(S, K, r, sigma, T)

    if option_type == "CE":
        return norm_cdf(d_1)

    else:
        return norm_cdf(d_1) - 1


# -----------------------------
# Black76 price
# -----------------------------
def option_price(S, K, r, sigma, T, option_type):

    d_1 = d1(S, K, r, sigma, T)
    d_2 = d_1 - sigma * math.sqrt(T)

    if option_type == "CE":
        return S * norm_cdf(d_1) - K * math.exp(-r*T) * norm_cdf(d_2)

    else:
        return K * math.exp(-r*T) * norm_cdf(-d_2) - S * norm_cdf(-d_1)


# -----------------------------
# Implied Volatility
# -----------------------------
def implied_volatility(price, S, K, r, T, option_type):

    sigma = 0.3

    for i in range(100):

        price_est = option_price(S, K, r, sigma, T, option_type)

        vega = S * math.sqrt(T) * math.exp(-0.5 * d1(S,K,r,sigma,T)**2) / math.sqrt(2*math.pi)

        if vega == 0:
            return None

        sigma = sigma - (price_est - price) / vega

        if abs(price_est - price) < 0.0001:
            return sigma

    return None


# -----------------------------
# Main function
# -----------------------------
def calculate_greeks(S, K, price, expiry, option_type):

    r = 0.06

    T = (expiry - datetime.now()).total_seconds() / (365*24*3600)

    if T <= 0:
        return None, None

    iv = implied_volatility(price, S, K, r, T, option_type)

    if iv is None:
        return None, None

    d = delta(S, K, r, iv, T, option_type)

    return iv, d