import requests
from bs4 import BeautifulSoup
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

TOKEN = "8993898662:AAG2cNJoFnJwOYv3tPqxD0mtBOub5cOxtoE"


# =========================
# SCRAPER SEGURO
# =========================

def scrape_product(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # =====================
        # TÍTULO
        # =====================
        title_tag = soup.find("meta", property="og:title")

        if title_tag and title_tag.get("content"):
            title = title_tag["content"]
        else:
            title = soup.title.string.strip() if soup.title else "Produto não encontrado"

        # =====================
        # IMAGEM
        # =====================
        img_tag = soup.find("meta", property="og:image")

        if img_tag and img_tag.get("content"):
            image = img_tag["content"]
        else:
            image = None

        # =====================
        # PREÇO (BÁSICO E ESTÁVEL)
        # =====================
        text = soup.get_text()

        match = re.search(r"R\$\s?\d+[.,]?\d*", text)

        if match:
            price = match.group()
        else:
            price = "Ver no link"

        return {
            "title": title,
            "image": image,
            "price": price,
            "link": url
        }

    except Exception as e:
        print("SCRAP ERROR:", e)

        return {
            "title": "Erro ao carregar produto",
            "image": None,
            "price": "Ver no link",
            "link": url
        }


# =========================
# FORMATAÇÃO REX TECH
# =========================

def format_message(p):
    return f"""
⚡ REX TECH DEAL ⚡

📦 {p['title']}
💰 {p['price']}
🏷 Cupom: ver no link

━━━━━━━━━━━━━━
🧬 Rex Tech Bot
"""


# =========================
# HANDLER TELEGRAM
# =========================

def handle(update: Update, context: CallbackContext):
    url = update.message.text

    if "http" not in url:
        update.message.reply_text("Envie um link válido.")
        return

    product = scrape_product(url)

    caption = format_message(product)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Comprar agora", url=product["link"])]
    ])

    # Se tiver imagem manda foto
    if product["image"]:
        update.message.reply_photo(
            photo=product["image"],
            caption=caption,
            reply_markup=keyboard
        )
    else:
        update.message.reply_text(caption, reply_markup=keyboard)


# =========================
# START BOT
# =========================

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))

updater.start_polling()
updater.idle()
