import re
from bot.config import AMBIGUOUS_PRODUCTS

def resolve_ambiguous_products(products_list):

    result = {}
    
    for product in products_list:
        product_lower = product.lower().strip()
        matched = None
        
        if product_lower in AMBIGUOUS_PRODUCTS:
            matched = product_lower
        else:
            for key in AMBIGUOUS_PRODUCTS:
                if key in product_lower or product_lower in key:
                    matched = key
                    break
        
        if matched:
            result[product] = AMBIGUOUS_PRODUCTS[matched]
        else:
            result[product] = None
    
    return result

def is_ambiguous(product):
    product_lower = product.lower()
    for key in AMBIGUOUS_PRODUCTS:
        if key in product_lower or product_lower in key:
            return True
    return False