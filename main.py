from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8993898662:AAG2cNJoFnJwOYv3tPqxD0mtBOub5cOxtoE"

async def receber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = """
🔥 OFERTA TECH 🔥

💰 Bot funcionando!
"""

    await update.message.reply_text(texto)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, receber))

print("Bot online...")
app.run_polling()
