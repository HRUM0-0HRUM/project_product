import random
from bot.config import BASE_PRICES, STORES

def get_base_price(product_name):

    product_lower = product_name.lower()
    
    if product_lower in BASE_PRICES:
        return BASE_PRICES[product_lower]
    
    for key, price in BASE_PRICES.items():
        if key in product_lower or product_lower in key:
            return price
    
    return 150

def get_product_price(product_name, store_name):

    base_price = get_base_price(product_name)
    store_coef = STORES[store_name]["price_coef"]
    
    variation = random.uniform(0.9, 1.1)
    
    final_price = round(base_price * store_coef * variation, 2)
    return final_price

def get_all_prices_for_product(product_name):

    prices = {}
    for store_name in STORES:
        prices[store_name] = get_product_price(product_name, store_name)
    return prices