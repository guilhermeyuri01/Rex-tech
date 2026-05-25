import requests
from bs4 import BeautifulSoup
import re

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)

# =========================
# CONFIG
# =========================

TOKEN = ":8993898662:AAFEPMd414DDI767a71F65MT3wqutBaVMH4"

GROUP_ID = -5113725387


# =========================
# SCRAPER
# =========================

def get_image(soup):
    img = soup.find("meta", property="og:image")

    if img and img.get("content"):
        return img["content"]

    return None


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


def scrape_product(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)

        soup = BeautifulSoup(r.text, "html.parser")

        # título
        title_tag = soup.find("meta", property="og:title")

        if title_tag and title_tag.get("content"):
            title = title_tag["content"]
        else:
            title = soup.title.string.strip()

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
        print("ERRO:", e)

        return {
            "title": "Erro ao pegar produto",
            "image": None,
            "price": "Ver no link",
            "link": url
        }


# =========================
# FORMATAÇÃO
# =========================

def format_message(product):
    return f"""
🔥 OFERTA ENCONTRADA 🔥

📦 {product['title']}

💰 {product['price']}

🛒 Link:
{product['link']}

━━━━━━━━━━━━━━
🧬 Rex Tech Deals
"""


# =========================
# RECEBER LINK
# =========================

def handle(update: Update, context: CallbackContext):
    url = update.message.text

    if "http" not in url:
        update.message.reply_text("Envie um link válido.")
        return

    product = scrape_product(url)

    text = format_message(product)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Aprovar",
                callback_data=f"approve|{url}"
            ),

            InlineKeyboardButton(
                "❌ Recusar",
                callback_data="reject"
            )
        ]
    ])

    if product["image"]:
        context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=product["image"],
            caption=text,
            reply_markup=keyboard
        )

    else:
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            reply_markup=keyboard
        )

    update.message.reply_text("✅ Oferta enviada para aprovação.")


# =========================
# BOTÕES
# =========================

def button_click(update: Update, context: CallbackContext):
    query = update.callback_query

    query.answer()

    data = query.data

    # APROVAR
    if data.startswith("approve"):

        url = data.split("|")[1]

        product = scrape_product(url)

        text = format_message(product)

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🛒 Comprar Agora",
                    url=product["link"]
                )
            ]
        ])

        try:

            if product["image"]:

                context.bot.send_photo(
                    chat_id=GROUP_ID,
                    photo=product["image"],
                    caption=text,
                    reply_markup=keyboard
                )

            else:

                context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=text,
                    reply_markup=keyboard
                )

            query.edit_message_text("✅ Oferta aprovada e enviada.")

        except Exception as e:

            query.edit_message_text(f"Erro: {e}")

    # RECUSAR
    elif data == "reject":

        query.edit_message_text("❌ Oferta recusada.")


# =========================
# START
# =========================

updater = Updater(TOKEN, use_context=True)

# remove webhook antigo
updater.bot.delete_webhook(drop_pending_updates=True)

dp = updater.dispatcher

dp.add_handler(
    MessageHandler(
        Filters.text & ~Filters.command,
        handle
    )
)

dp.add_handler(
    CallbackQueryHandler(button_click)
)

print("BOT ONLINE")

updater.start_polling(drop_pending_updates=True)
updater.idle()
