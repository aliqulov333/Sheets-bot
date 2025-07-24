import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.client.session.aiohttp import AiohttpSession  # ✅ to‘g‘ri session
from aiohttp import TCPConnector
from google.oauth2 import service_account
from googleapiclient.discovery import build

# === Telegram token va admin ID ===
BOT_TOKEN = "7086039869:AAEz0n4EGjE-2BtjdnveSJndEdmIOiLVJXM"
ADMIN_ID = 1259148208

# === Google Sheets parametrlari ===
SHEET_ID = '1WVjMFWnishN96wCvhtdQelWNTjvUW-aJAcOfXkkKUvI'
RANGE_NAME = 'Лист1!A1:Z1000'
CHECK_INTERVAL = 20
SERVICE_ACCOUNT_FILE = 'service_account.json'

# === Loglar ===
logging.basicConfig(level=logging.INFO)

# === Global o'zgaruvchilar ===
chat_ids = set()
old_row_count = 0

# === Google Sheets API sozlash ===
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
sheet_service = build('sheets', 'v4', credentials=creds, cache_discovery=False).spreadsheets()

# === Yangi qatorlarni tekshiruvchi funksiya ===
async def check_new_data(bot: Bot):
    global old_row_count
    await asyncio.sleep(5)
    while True:
        try:
            result = sheet_service.values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
            values = result.get("values", [])
            row_count = len(values)

            if row_count > old_row_count:
                new_rows = values[old_row_count:]
                for row in new_rows:
                    msg = "🆕 Yangi LEAD:\n" + "\n".join([f"{i+1}) {cell}" for i, cell in enumerate(row)])
                    for chat_id in chat_ids:
                        await bot.send_message(chat_id=chat_id, text=msg)
                old_row_count = row_count

        except Exception as e:
            logging.error(f"[Xatolik] Sheets tekshiruvda muammo: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

# === Foydalanuvchi /start yuborganda ===
async def start_monitoring(message: Message):
    if message.chat.id != ADMIN_ID:
        await message.answer("❌ Sizga bu botdan foydalanishga ruxsat yo‘q.")
        return
    chat_ids.add(message.chat.id)
    await message.answer("✅ Monitoring faollashtirildi! Har 20 soniyada yangi LEADlar tekshiriladi.")

# === Asosiy ishga tushirish funksiyasi ===
async def main():
    proxy_url = "http://10.0.4.152:3128"  # 🌐 ← Shu yerga o'zingizning PROXY manzilingizni yozing

    connector = TCPConnector()
    session = AiohttpSession(proxy=proxy_url, connector=connector)

    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()
    dp.message.register(start_monitoring)

    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_new_data(bot))
    await dp.start_polling(bot)

    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
