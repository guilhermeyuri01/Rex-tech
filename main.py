import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8993898662:AAHUS-UCvA8B59twZmS4ozrPFU16UrjH-Ww"

async def receber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text

    texto = f"""
🔥 OFERTA TECH 🔥

🛒 Produto encontrado:
{link}

💰 Melhor preço encontrado!
"""

    await update.message.reply_text(texto)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, receber))

print("Bot online...")
app.run_polling()
