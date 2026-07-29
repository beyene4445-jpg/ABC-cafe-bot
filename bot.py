import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardRemove
from aiohttp import web

# ቶከኖችህ እና የቻት ID ዎች
BOT_TOKEN = "8949760536:AAH-ptN3CVOdG210xRYAeIJwIOib0Yoa-E8"

# 1. የካሺር ቻት ID (ገንዘብ እና አጠቃላይ ሂሳብ የሚደርሰው)
CASHIER_CHAT_ID = 8053830568  # @peterdec2

# 2. የኩሽና ቻት ID (ምግቦቹ ብቻ አዘጋጅተው እንዲደርሳቸው የሚፈልጉበት)
KITCHEN_CHAT_ID = 8674073724  # የኩሽናውን ID እዚህጋ አስገባ (ለጊዜው በእጅህ እንዲሞከር በአንድ ላይ ተቀምጧል)

# ለጊዜው በሙከራ ደረጃ (Test Mode) የሚሰራው የ Chapa ቶከን
PROVIDER_TOKEN = "6141645565:TEST:97h5BwIS5k3cutoKIQPp"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# በኢትዮጵያ የተለመዱ 12 ምግቦችና መጠጦች (ዋጋ በሳንቲም)
MENU = {
    "burger": {"name": "🍔 በርገር (Burger)", "price": 25000},
    "pizza": {"name": "🍕 ፒዛ (Pizza)", "price": 35000},
    "shiro": {"name": "🥘 ሽሮ ተጋቢኖ", "price": 18000},
    "tibbs": {"name": "🥩 ልዩ ጥብስ (Tibbs)", "price": 40000},
    "firfir": {"name": "🍲 ቋንጣ ፍርፍር", "price": 20000},
    "beyaynetu": {"name": "🥗 የጾም በያይነቱ", "price": 22000},
    "cake": {"name": "🍰 ኬክ (Cake)", "price": 12000},
    "macchiato": {"name": "☕ ማኪያቶ", "price": 9000},
    "avocado": {"name": "🥑 አቮካዶ ጁስ", "price": 14000},
    "spris": {"name": "🍹 ስፕሪስ ጁስ", "price": 15000},
    "shahi": {"name": "🍵 ሻይ (Tea)", "price": 4000},
    "soda": {"name": "🥤 ለስላሳ (Soda)", "price": 6000}
}

user_carts = {}

# በተኖቹን በየመስመሩ 2 እያደረገ የሚያምር ሌአውት የሚሰራ ፈንክሽን
def get_menu_keyboard(chat_id):
    cart = user_carts.get(chat_id, {k: 0 for k in MENU})
    keyboard = []
    row = []
    
    for item, data in MENU.items():
        qty = cart.get(item, 0)
        btn_text = f"{data['name']} [{qty}]" if qty > 0 else data['name']
        btn = InlineKeyboardButton(text=btn_text, callback_data=f"add_{item}")
        row.append(btn)
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
            
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton(text="🛒 ሂሳብ ድምር ክፈል (Checkout)", callback_data="checkout")])
    keyboard.append([InlineKeyboardButton(text="🗑️ ቅርጫት አጽዳ (Clear)", callback_data="clear_cart")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(Command("start"))
async def start_command(message: Message):
    user_carts[message.chat.id] = {k: 0 for k in MENU}
    
    welcome_text = (
        "እንኳን ወደ ABC ካፌ መደበኛ ማዘዣ ቦት በደህና መጡ! ☕🍔\n\n"
        "የምግብ ዝርዝር ለማየት እና ለማዘዝ /menu ይበሉ።\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💻 **Developed by:** Petros Beyene (@peterdec2)\n"
        "🚀 **Powered by:** Python & Chapa (Test Mode)"
    )
    
    await message.answer(
        text=welcome_text,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )

@dp.message(Command("menu"))
async def menu_command(message: Message):
    if message.chat.id not in user_carts:
        user_carts[message.chat.id] = {k: 0 for k in MENU}
    await message.answer("🛒 እባክዎ ከታች ካለው ዝርዝር ውስጥ ማዘዝ የሚፈልጉትን ምግብ ይጫኑ፦", reply_markup=get_menu_keyboard(message.chat.id))

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_item_handler(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    item = callback_query.data.replace("add_", "")
    
    if item not in MENU:
        return
        
    if chat_id not in user_carts:
        user_carts[chat_id] = {k: 0 for k in MENU}
        
    user_carts[chat_id][item] += 1
    await callback_query.message.edit_reply_markup(reply_markup=get_menu_keyboard(chat_id))
    await callback_query.answer(f"{MENU[item]['name']} ተጨምሯል!")

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart_handler(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_carts[chat_id] = {k: 0 for k in MENU}
    await callback_query.message.edit_reply_markup(reply_markup=get_menu_keyboard(chat_id))
    await callback_query.answer("ቅርጫትዎ ጸድቷል!")

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout_handler(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    cart = user_carts.get(chat_id, {k: 0 for k in MENU})
    prices = []
    description_parts = []
    
    for item, qty in cart.items():
        if qty > 0:
            item_total = MENU[item]["price"] * qty
            clean_name = MENU[item]["name"].split("(")[0].strip()
            prices.append(LabeledPrice(label=f"{clean_name} x{qty}", amount=item_total))
            description_parts.append(f"{clean_name} ({qty} ፍሬ)")
            
    if not prices:
        await callback_query.answer("⚠️ እባክዎ መጀመሪያ ቢያንስ አንድ ምግብ ይምረጡ!", show_alert=True)
        return
        
    await callback_query.answer()
    description = "የታዘዙ ምግቦች፦ " + ", ".join(description_parts)
    await bot.send_invoice(
        chat_id=chat_id,
        title="ABC Cafe - የትዕዛዝ ክፍያ",
        description=description,
        payload="cafe_multi_order_payload",
        provider_token=PROVIDER_TOKEN,
        currency="ETB",
        prices=prices,
        start_parameter="cafe-order"
    )

@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(lambda message: message.successful_payment is not None)
async def successful_payment_handler(message: Message):
    chat_id = message.chat.id
    cart = user_carts.get(chat_id, {k: 0 for k in MENU})
    
    customer_name = message.from_user.full_name
    customer_username = f"@{message.from_user.username}" if message.from_user.username else "የለውም"
    total_amount = message.successful_payment.total_amount / 100
    
    order_details = []
    for item, qty in cart.items():
        if qty > 0:
            clean_name = MENU[item]["name"].split("(")[0].strip()
            order_details.append(f"• {clean_name}፦ {qty} ፍሬ")
            
    order_str = "\n".join(order_details)
    
    # 1. ለካሺር የሚሄድ መልዕክት (የገንዘብ መጠን እና አጠቃላይ ሂሳብ ያለው)
    cashier_message = (
        f"💰 **አዲስ ክፍያ ደርሷል (ለካሺር)** 💰\n\n"
        f"👤 **ደንበኛ፦** {customer_name} ({customer_username})\n"
        f"💵 **ጠቅላላ የተከፈለ፦** {total_amount:,.2f} ETB\n\n"
        f"🛍️ **የታዘዙ ምግቦች ዝርዝር፦**\n{order_str}\n\n"
        f"✅ ክፍያው በ Chapa አውቶማቲክ ሲስተም ተረጋግጧል!"
    )
    
    # 2. ለኩሽና የሚሄድ መልዕክት (ምግቦቹ በግልጽ የሚታዩበት የትዕዛዝ ማዘዣ)
    kitchen_message = (
        f"🍳 **አዲስ ትዕዛዝ ወደ ኩሽና ደርሷል!** 🍳\n\n"
        f"👤 **ለደንበኛ፦** {customer_name}\n\n"
        f"📋 **ማዘጋጀት ያለብዎት ምግቦች፦**\n{order_str}\n\n"
        f"🚀 እባክዎ በፍጥነት አዘጋጅተው ያቅርቡ!"
    )
    
    try:
        # መልዕክቱን ለሁለቱም በግል ይልካል
        await bot.send_message(chat_id=CASHIER_CHAT_ID, text=cashier_message, parse_mode="Markdown")
        await bot.send_message(chat_id=KITCHEN_CHAT_ID, text=kitchen_message, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Failed to send order notifications: {e}")

    user_carts[chat_id] = {k: 0 for k in MENU}
    await message.answer("🎉 ክፍያዎ አውቶማቲክ በሆነ መንገድ በተሳካ ሁኔታ ተረጋግጧል!\n\nምግብዎ እየተዘጋጀ ነው።")

async def handle_render(request):
    return web.Response(text="Bot is running smoothly in Test Mode. Developed by Petros Beyene.")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_render)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
