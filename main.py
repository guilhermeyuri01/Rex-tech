import requests
from bs4 import BeautifulSoup
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

TOKEN = "8993898662:AAG2cNJoFnJwOYv3tPqxD0mtBOub5cOxtoE"

# -------- SCRAPER --------
def scrape_product(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.title.string if soup.title else "Produto"

    img = ""
    meta_img = soup.find("meta", property="og:image")
    if meta_img:
        img = meta_img.get("content")

    text = soup.get_text()
    price = "Não encontrado"

    match = re.search(r"R\$\s?\d+[\.,]?\d*", text)
    if match:
        price = match.group()

    return {
        "title": title,
        "image": img,
        "price": price,
        "link": url
    }

# -------- FORMAT --------
def format_msg(p):
    return f"""
⚡ REX TECH DEAL ⚡

📦 {p['title']}
💰 {p['price']}
🔥 Oferta automática

━━━━━━━━━━━━━━
🧬 Rex Tech
"""

# -------- HANDLER --------
def handle(update: Update, context: CallbackContext):
    url = update.message.text

    if "http" not in url:
        update.message.reply_text("Envie um link válido.")
        return

    p = scrape_product(url)
    msg = format_msg(p)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Comprar agora", url=p["link"])]
    ])

    if p["image"]:
        update.message.reply_photo(
            photo=p["image"],
            caption=msg,
            reply_markup=keyboard
        )
    else:
        update.message.reply_text(msg, reply_markup=keyboard)

# -------- RUN --------
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))

updater.start_polling()
updater.idle()
