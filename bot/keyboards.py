from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_ambiguous_keyboard(original_product, variants):

    keyboard = []
    for variant in variants:
        keyboard.append([InlineKeyboardButton(
            variant, 
            callback_data=f"select_{original_product}_{variant}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        "Пропустить (выбрать первый вариант)", 
        callback_data=f"skip_{original_product}"
    )])
    
    return InlineKeyboardMarkup(keyboard)

def get_confirm_keyboard():

    keyboard = [
        [
            InlineKeyboardButton("Подтвердить", callback_data="confirm"),
            InlineKeyboardButton("Отмена", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)