import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from bot.core.product_resolver import resolve_ambiguous_products
from bot.core.cart_calculator import calculate_cart, format_comparison_message
from bot.storage.session_storage import create_session, get_session, update_session, delete_session
from bot.keyboards import get_ambiguous_keyboard, get_confirm_keyboard

logger = logging.getLogger(__name__)


user_carts = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}!\n\n"
        "Я помогу тебе сравнить цены в разных магазинах и найти самую выгодную корзину.\n\n"
        "*Как это работает:*\n"
        "1. Отправь мне список продуктов (через запятую)\n"
        "2. Если какой-то товар описан размыто, я предложу уточнить\n"
        "3. Я сравню цены в Пятёрочке, Перекрёстке, Ленте, Самокате и Яндекс Лавке\n"
        "4. Получи результат с итоговой суммой и экономией\n\n"
        "*Пример:* `молоко, хлеб, яйца, сыр, масло`\n\n"
        "Готов? Отправляй список продуктов!",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "*Справка*\n\n"
        "• Отправь список продуктов через запятую\n"
        "• Можно указывать количество: '2 яйца', '500г сыра'\n"
        "• Размытые товары (например, 'молоко') будут уточнены\n"
        "• Команда /start — начать заново\n"
        "• Команда /cancel — отменить текущий заказ\n\n"
        "*Доступные магазины:*\n"
        "• Пятёрочка\n"
        "• Перекрёсток\n"
        "• Лента\n"
        "• Самокат\n"
        "• Яндекс Лавка",
        parse_mode="Markdown"
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    delete_session(user_id)
    if user_id in user_carts:
        del user_carts[user_id]
    await update.message.reply_text(
        "Действие отменено. Чтобы начать заново, отправь новый список продуктов."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not text:
        await update.message.reply_text("Пожалуйста, отправь список продуктов через запятую.")
        return
    

    products = [p.strip() for p in text.split(",") if p.strip()]
    
    if not products:
        await update.message.reply_text("Не удалось распознать список. Попробуй ещё раз.")
        return
    
    logger.info(f"User {user_id} sent products: {products}")
    

    ambiguous_map = resolve_ambiguous_products(products)
    ambiguous_items = {k: v for k, v in ambiguous_map.items() if v is not None}
    
    if ambiguous_items:

        session_data = {
            "original_products": products,
            "ambiguous_map": ambiguous_items,
            "resolved_products": {k: None for k in ambiguous_items.keys()},
            "step": 0,
            "clear_products": [p for p in products if p not in ambiguous_items]
        }
        create_session(user_id, session_data)
        
        await ask_next_ambiguous(update, context, user_id)
    else:
        await calculate_and_send_result(update, context, products)

async def ask_next_ambiguous(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    session = get_session(user_id)
    if not session:
        return
    
    ambiguous_items = list(session["ambiguous_map"].items())
    current_step = session["step"]
    
    if current_step >= len(ambiguous_items):
        final_products = session["clear_products"].copy()
        for orig, chosen in session["resolved_products"].items():
            if chosen:
                final_products.append(chosen)
            else:
                final_products.append(session["ambiguous_map"][orig][0])
        
        delete_session(user_id)
        await calculate_and_send_result(update, context, final_products)
        return
    
    original_product, variants = ambiguous_items[current_step]
    
    from bot.keyboards import get_ambiguous_keyboard
    reply_markup = get_ambiguous_keyboard(original_product, variants)
    
    await update.message.reply_text(
        f"Уточните, пожалуйста, что вы имеете в виду под «{original_product}»:",
        reply_markup=reply_markup
    )

async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    session = get_session(user_id)
    if not session:
        await query.edit_message_text("⏰ Сессия истекла. Отправьте список заново.")
        return
    
    if data.startswith("select_"):
        _, original, chosen = data.split("_", 2)
        session["resolved_products"][original] = chosen
        session["step"] += 1
        update_session(user_id, session)
        
        await query.edit_message_text(f"Выбрано: {chosen}")
        
        await ask_next_ambiguous(query, context, user_id)
    
    elif data.startswith("skip_"):
        _, original = data.split("_", 1)
        session["resolved_products"][original] = None
        session["step"] += 1
        update_session(user_id, session)
        
        await query.edit_message_text(f"Пропущено, будет выбран первый вариант")
        await ask_next_ambiguous(query, context, user_id)

async def calculate_and_send_result(update: Update, context: ContextTypes.DEFAULT_TYPE, products_list):

    if isinstance(update, Update) and update.message:
        await update.message.reply_text("Рассчитываю стоимость корзины...")
    elif hasattr(update, 'edit_message_text'):
        await update.edit_message_text("Рассчитываю стоимость корзины...")
    
    cart_results = calculate_cart(products_list)
    
    message = format_comparison_message(cart_results)
    
    products_text = "\n\n📋 *Ваш список:*\n" + "\n".join(f"• {p}" for p in products_list)
    message += products_text
    
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(message, parse_mode="Markdown")
    else:
        await update.edit_message_text(message, parse_mode="Markdown")