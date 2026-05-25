import requests
from bs4 import BeautifulSoup
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

TOKEN = "8993898662:AAG2cNJoFnJwOYv3tPqxD0mtBOub5cOxtoE"


# =========================
# SCRAPER
# =========================

def get_image(soup):
    img = soup.find("meta", property="og:image")
    if img and img.get("content"):
        return img["content"]

    img = soup.find("meta", attrs={"name": "og:image"})
    if img and img.get("content"):
        return img["content"]

    return None


def scrape_product(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # TÍTULO
        title_tag = soup.find("meta", property="og:title")
        if title_tag and title_tag.get("content"):
            title = title_tag["content"]
        else:
            title = soup.title.string if soup.title else "Produto"

        # IMAGEM
        image = get_image(soup)

        # PREÇO (simples fallback)
        text = soup.get_text()
        match = re.search(r"R\$\s?\d+[.,]?\d*", text)
        price = match.group() if match else "Não encontrado"

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
            "price": "?",
            "link": url
        }


# =========================
# FORMATADOR REX TECH
# =========================

def format_message(p):
    return f"""
⚡ REX TECH DEAL ⚡

📦 {p['title']}
💰 {p['price']}
🔥 Oferta automática verificada

━━━━━━━━━━━━━━
🧬 Rex Tech Bot
"""


# =========================
# HANDLER TELEGRAM
# =========================

def handle(update: Update, context: CallbackContext):
    url = update.message.text

    if "http" not in url:
        update.message.reply_text("Envie um link válido de produto.")
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
