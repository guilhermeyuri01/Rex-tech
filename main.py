import requests
from bs4 import BeautifulSoup
import re

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    filters
)

# =========================
# CONFIG
# =========================

TOKEN = "8993898662:AAEThBQVbytvrVfgQayffhAyUUxlfIdlfMs"

# MUITO PROVAVELMENTE O CERTO É ASSIM:
GROUP_ID = -5113725387

pending_products = {}

# =========================
# PEGAR ID DO CHAT
# =========================

async def chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"ID DO CHAT: {update.effective_chat.id}"
    )

# =========================
# PEGAR IMAGEM
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
# EXTRAIR PREÇO
# =========================

def extract_price(soup):
    text = soup.get_text()

    patterns = [
        r"R\$\s?\d+[.,]?\d*",
        r"\$\s?\d+[.,]?\d*",
        r"\d+[.,]\d{2}"
    ]

    for p in patterns:
        match = re.search(p, text)

        if match:
            return match.group()

    return "Ver no link"

# =========================
# SCRAPER
# =========================

def scrape_product(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        # TÍTULO
        title_tag = soup.find(
            "meta",
            property="og
