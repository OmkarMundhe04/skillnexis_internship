import requests

def get_crypto_price(coin_id, currency="usd"):
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin_id, "vs_currencies": currency}
    response = requests.get(url, params=params)
    data = response.json()
    return data[coin_id][currency]

# Usage
btc_price = get_crypto_price("bitcoin", "usd")
eth_price = get_crypto_price("ethereum", "usd")

print(f"Bitcoin Price: ${btc_price}")
print(f"Ethereum Price: ${eth_price}")
