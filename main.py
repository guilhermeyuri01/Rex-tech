import requests
from bs4 import BeautifulSoup
import re
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
TOKEN = "8993898662:AAG2cNJoFnJwOYv3tPqxD0mtBOub5cOxtoE"


# =========================
# IMAGEM
# =========================

def get_image(soup):
    img = soup.find("meta", property="og:image")
    if img and img.get("content"):
        return img["content"]

    img = soup.find("meta", attrs={"name": "og:image"})
    if img and img.get("content"):
        return img["content"]

    return None


# =========================
# PREÇO MELHORADO
# =========================

def extract_price(soup):
    text = soup.get_text()

    # 1. regex comum
    patterns = [
        r"R\$\s?\d+[.,]?\d*",
        r"\$\s?\d+[.,]?\d*",
        r"\d+[.,]\d{2}"
    ]

    for p in patterns:
        match = re.search(p, text)
        if match:
            return match.group()

    # 2. tenta achar em scripts (mais forte)
    scripts = soup.find_all("script")

    for s in scripts:
        if s.string:
            if "price" in s.string.lower():
                try:
                    data = json.loads(s.string)
                    return str(data)
                except:
                    continue

    return "Não encontrado"


# =========================
# SCRAPER
# =========================

def scrape_product(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # título
        title_tag = soup.find("meta", property="og:title")
        if title_tag and title_tag.get("content"):
            title = title_tag["content"]
        else:
            title = soup.title.string if soup.title else "Produto"

        # imagem
        image = get_image(soup)

        # preço
        price = extract_price(soup)

        return {
            "title": title,
            "image": image,
            "price": price,
            "link": url
        }

    except Exception as e:
        print("ERROR:", e)
        return {
            "title": "Erro ao carregar produto",
            "image": None,
            "price": "?",
            "link": url
        }


# =========================
# MENSAGEM REX TECH
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
# TELEGRAM HANDLER
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

    if product["image"]:
        update.message.reply_photo(
            photo=product["image"],
            caption=caption,
            reply_markup=keyboard
        )
    else:
        update.message.reply_text(caption, reply_markup=keyboard)


# =========================
# RUN BOT
# =========================

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))

updater.start_polling()
updater.idle()
