from telegram.ext import Updater, CommandHandler

TOKEN = "8993898662:AAG2cNJoFnJwOYv3tPqxD0mtBOub5cOxtoE"

def start(update, context):
    update.message.reply_text("🔥 Bot funcionando!")

updater = Updater(TOKEN, use_context=True)

dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))

print("Bot online...")
updater.start_polling()
updater.idle()
