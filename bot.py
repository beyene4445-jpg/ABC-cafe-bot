import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, Message
from aiohttp import web

# ቶከኖችህ
BOT_TOKEN = "8949760536:AAH-ptN3CVOdG210xRYAeIJwIOib0Yoa-E8"
PROVIDER_TOKEN = "6141645565:TEST:97h5BwIS5k3cutoKIQPp"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("እንኳን ወደ ABC ካፌ መደበኛ ማዘዣ ቦት በደህና መጡ! ☕🍔\n\nምግብ ለማዘዝ /order ይበሉ።")

@dp.message(Command("order"))
async def order_command(message: Message):
    prices = [LabeledPrice(label="በርገር፣ ፒዛ እና ኬክ (Combo)", amount=69000)] # 690.00 ETB
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="ABC Cafe - የትዕዛዝ ክፍያ",
        description="የመረጧቸው ምግቦች አጠቃላይ ድምር። እባክዎ ከታች ያለውን የክፍያ በተን በመንካት ይክፈሉ።",
        payload="cafe_combo_order_payload",
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
    await message.answer("🎉 ክፍያዎ አውቶማቲክ በሆነ መንገድ በተሳካ ሁኔታ ተረጋግጧል!\n\nትዕዛዝዎ ወደ ኩሽና ተላልፏል።")

# Render እንዳይዘጋብን ፖርት (Port) የሚከፍት አጭር ኮድ
async def handle_render(request):
    return web.Response(text="Bot is running smoothly!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_render)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    asyncio.create_task(start_web_server()) # ሰርቨሩን በጀርባ ያስነሳል
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
