from bot.config import STORES
from bot.core.price_fetcher import get_product_price

def calculate_cart(products_list):

    results = []
    
    for store_name, store_info in STORES.items():
       
        products_total = 0
        product_details = []
        
        for product in products_list:
            price = get_product_price(product, store_name)
            products_total += price
            product_details.append({
                "name": product,
                "price": price
            })
        
        delivery_fee = store_info["delivery_fee"]
        pickup_fee = store_info["pickup_fee"]
        
        min_order = store_info["min_order"]
        if products_total < min_order:
            pass
        
        grand_total = products_total + delivery_fee + pickup_fee
        
        results.append({
            "store": store_name,
            "products_total": round(products_total, 2),
            "delivery_fee": delivery_fee,
            "pickup_fee": pickup_fee,
            "grand_total": round(grand_total, 2),
            "product_details": product_details,
            "min_order": min_order
        })
    
    results.sort(key=lambda x: x["grand_total"])
    
    return results

def format_comparison_message(cart_results):
    """
    Форматирует результаты сравнения в красивое сообщение
    """
    if not cart_results:
        return "Не удалось рассчитать стоимость. Попробуйте ещё раз."
    
    message = "*Сравнение магазинов*\n\n"
    
    for i, result in enumerate(cart_results):
        # Эмодзи для первого места
        if i == 0:
            message += "*Лучший выбор*\n"
        
        message += f"*{result['store']}*\n"
        message += f"Продукты: {result['products_total']} руб\n"
        
        if result['delivery_fee'] > 0:
            message += f"Доставка: {result['delivery_fee']} руб\n"
        if result['pickup_fee'] > 0:
            message += f"Сборка заказа: {result['pickup_fee']} руб\n"
        
        if result['min_order'] > 0 and result['products_total'] < result['min_order']:
            message += f"*Минимальная сумма заказа: {result['min_order']} руб*\n"
        
        message += f"*Итого: {result['grand_total']} руб*\n"
        message += "─" * 25 + "\n"
    
    # Добавляем экономию
    best = cart_results[0]
    worst = cart_results[-1]
    savings = worst['grand_total'] - best['grand_total']
    message += f"\n*Экономия*: до {int(savings)} руб, если заказать в {best['store']}"
    
    return message