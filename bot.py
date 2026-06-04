import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiohttp import web

# ቶከኖችህ
BOT_TOKEN = "8949760536:AAH-ptN3CVOdG210xRYAeIJwIOib0Yoa-E8"
PROVIDER_TOKEN = "6141645565:TEST:97h5BwIS5k3cutoKIQPp"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# የምግብ ዝርዝር እና ዋጋ (በሳንቲም)
MENU = {
    "burger": {"name": "በርገር (Burger)", "price": 25000},       # 250 ETB
    "pizza": {"name": "ፒዛ (Pizza)", "price": 35000},          # 350 ETB
    "macchiato": {"name": "ማኪያቶ (Macchiato)", "price": 9000}   # 90 ETB
}

user_carts = {}

def get_menu_keyboard(chat_id):
    cart = user_carts.get(chat_id, {"burger": 0, "pizza": 0, "macchiato": 0})
    keyboard = [
        [InlineKeyboardButton(text=f"🍔 burger (+1) [ያዘዙት፦ {cart['burger']}]", callback_data="add_burger")],
        [InlineKeyboardButton(text=f"🍕 pizza (+1) [ያዘዙት፦ {cart['pizza']}]", callback_data="add_pizza")],
        [InlineKeyboardButton(text=f"☕ macchiato (+1) [ያዘዙት፦ {cart['macchiato']}]", callback_data="add_macchiato")],
        [InlineKeyboardButton(text="🛒 ሂሳብ ድምር ክፈል (Checkout)", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑️ ቅርጫት አጽዳ (Clear)", callback_data="clear_cart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(Command("start"))
async def start_command(message: Message):
    user_carts[message.chat.id] = {"burger": 0, "pizza": 0, "macchiato": 0}
    await message.answer("እንኳን ወደ ABC ካፌ መደበኛ ማዘዣ ቦት በደህና መጡ! ☕🍔\n\nየምግብ ዝርዝር ለማየት እና ለማዘዝ /menu ይበሉ።")

@dp.message(Command("menu"))
async def menu_command(message: Message):
    if message.chat.id not in user_carts:
        user_carts[message.chat.id] = {"burger": 0, "pizza": 0, "macchiato": 0}
    await message.answer("🛒 እባክዎ ከታች ካለው ዝርዝር ውስጥ ማዘዝ የሚፈልጉትን ምግብ ይጫኑ፦", reply_markup=get_menu_keyboard(message.chat.id))

@dp.callback_query(lambda c: c.data in ["add_burger", "add_pizza", "add_macchiato"])
async def add_item_handler(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    if chat_id not in user_carts:
        user_carts[chat_id] = {"burger": 0, "pizza": 0, "macchiato": 0}
    item = callback_query.data.replace("add_", "")
    user_carts[chat_id][item] += 1
    await callback_query.message.edit_reply_markup(reply_markup=get_menu_keyboard(chat_id))
    await callback_query.answer(f"{MENU[item]['name']} ተጨምሯል!")

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart_handler(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_carts[chat_id] = {"burger": 0, "pizza": 0, "macchiato": 0}
    await callback_query.message.edit_reply_markup(reply_markup=get_menu_keyboard(chat_id))
    await callback_query.answer("ቅርጫትዎ ጸድቷል!")

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout_handler(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    cart = user_carts.get(chat_id, {"burger": 0, "pizza": 0, "macchiato": 0})
    prices = []
    description_parts = []
    for item, qty in cart.items():
        if qty > 0:
            item_total = MENU[item]["price"] * qty
            prices.append(LabeledPrice(label=f"{MENU[item]['name']} x{qty}", amount=item_total))
            description_parts.append(f"{MENU[item]['name']} ({qty} ፍሬ)")
    if not prices:
        await callback_query.answer("⚠️ እባክዎ መጀመሪያ ቢያንስ አንድ ምግብ ይምረጡ!", show_alert=True)
        return
    await callback_query.answer()
    description = "የታዘዙ ምግቦች ዝርዝር፦ " + ", ".join(description_parts)
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
    user_carts[chat_id] = {"burger": 0, "pizza": 0, "macchiato": 0}
    await message.answer("🎉 ክፍያዎ አውቶማቲክ በሆነ መንገድ በተሳካ ሁኔታ ተረጋግጧል!\n\nትዕዛዝዎ ወደ ኩሽና ተላልፏል።")

async def handle_render(request):
    return web.Response(text="Bot is running with dynamic menu layout!")

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
