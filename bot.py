import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, CallbackContext

TOKEN = os.getenv("TOKEN")  # دریافت توکن از Railway

bot = Bot(token=TOKEN)
photo_votes = {}  # دیکشنری برای ذخیره عکس‌ها و تعداد رأی

async def handle_photo(update: Update, context: CallbackContext):
    """وقتی عکسی در گروه ارسال شد، بهش ❤️ اضافه کن و ذخیره کن."""
    message = update.message
    if message.photo:
        await message.reply_text("✅ عکس برای رأی‌گیری اضافه شد!")
        await message.react("❤️")  # اضافه کردن واکنش ❤️

        # ذخیره اطلاعات عکس
        photo_votes[message.message_id] = {"votes": 0, "timestamp": datetime.utcnow(), "file_id": message.photo[-1].file_id}

async def count_votes(context: CallbackContext):
    """بعد از 48 ساعت، عکس‌هایی که بیشترین ❤️ رو دارن اعلام کن."""
    now = datetime.utcnow()
    results = []

    for msg_id, data in list(photo_votes.items()):
        if now - data["timestamp"] > timedelta(hours=48):  # بررسی ۴۸ ساعت گذشته
            message = await bot.get_chat(context.job.chat_id).get_message(msg_id)
            vote_count = sum(1 for reaction in message.reactions if reaction.emoji == "❤️")

            if vote_count > 0:
                results.append((vote_count, data["file_id"]))
            
            del photo_votes[msg_id]  # حذف عکس‌های قدیمی

    # ارسال نتایج
    if results:
        results.sort(reverse=True, key=lambda x: x[0])
        text = "🏆 **نتایج رأی‌گیری:**\n"
        for i, (votes, file_id) in enumerate(results[:5], start=1):
            text += f"{i}. ❤️ {votes} رأی\n"
            await bot.send_photo(context.job.chat_id, file_id)

        await bot.send_message(context.job.chat_id, text)

async def main():
    """اجرای ربات."""
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # تنظیم تایمر برای بررسی رأی‌گیری هر ۱ ساعت
    job_queue = app.job_queue
    job_queue.run_repeating(count_votes, interval=3600, first=10)
    
    print("✅ ربات اجرا شد!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
