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
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# =========================
# CONFIG
# =========================

TOKEN = "8993898662:AAFEPMd414DDI767a71F65MT3wqutBaVMH4"

ADMIN_ID = 123456789
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

        title_tag = soup.find("meta", property="og:title")

        if title_tag and title_tag.get("content"):
            title = title_tag["content"]
        else:
            title = soup.title.string.strip()

        image = get_image(soup)

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

━━━━━━━━━━━━━━
🧬 Rex Tech Deals
"""


# =========================
# RECEBER LINK
# =========================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "http" not in url:
        await update.message.reply_text("Envie um link válido.")
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

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=product["image"],
            caption=text,
            reply_markup=keyboard
        )

    else:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            reply_markup=keyboard
        )

    await update.message.reply_text(
        "✅ Oferta enviada para aprovação."
    )


# =========================
# BOTÕES
# =========================

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

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

                await context.bot.send_photo(
                    chat_id=GROUP_ID,
                    photo=product["image"],
                    caption=text,
                    reply_markup=keyboard
                )

            else:

                await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=text,
                    reply_markup=keyboard
                )

            await query.edit_message_text(
                "✅ Oferta aprovada e enviada."
            )

        except Exception as e:

            await query.edit_message_text(
                f"Erro: {e}"
            )

    # RECUSAR
    elif data == "reject":

        await query.edit_message_text(
            "❌ Oferta recusada."
        )


# =========================
# START
# =========================

app = Application.builder().token(TOKEN).build()

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle
    )
)

app.add_handler(
    CallbackQueryHandler(button_click)
)

print("BOT ONLINE")

app.run_polling(drop_pending_updates=True)
