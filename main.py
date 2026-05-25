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
    filters
)

# =========================
# CONFIG
# =========================

TOKEN = "8993898662:AAEThBQVbytvrVfgQayffhAyUUxlfIdlfMs"
GROUP_ID = 5113725387

pending_products = {}

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
            property="og:title"
        )

        if title_tag and title_tag.get("content"):
            title = title_tag["content"]
        else:
            title = (
                soup.title.string.strip()
                if soup.title
                else "Produto não encontrado"
            )

        # IMAGEM
        image = get_image(soup)

        # PREÇO
        price = extract_price(soup)

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
# FORMATAR MSG
# =========================

def format_message(p):
    return f"""
⚡ REX TECH DEAL ⚡

📦 {p['title']}
💰 {p['price']}

━━━━━━━━━━━━━━
🧬 Rex Tech Bot
"""

# =========================
# RECEBER LINK
# =========================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    url = update.message.text

    if "http" not in url:
        await update.message.reply_text(
            "Envie um link válido."
        )
        return

    product = scrape_product(url)

    msg_id = str(update.message.message_id)

    pending_products[msg_id] = product

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Aprovar",
                callback_data=f"approve_{msg_id}"
            ),

            InlineKeyboardButton(
                "❌ Recusar",
                callback_data=f"reject_{msg_id}"
            )
        ]
    ])

    caption = format_message(product)

    try:
        if product["image"]:
            await update.message.reply_photo(
                photo=product["image"],
                caption=caption,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                caption,
                reply_markup=keyboard
            )

    except Exception as e:
        print("ERRO FOTO:", e)

        await update.message.reply_text(
            caption,
            reply_markup=keyboard
        )

# =========================
# BOTÕES
# =========================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    data = query.data

    # =====================
    # APROVAR
    # =====================

    if data.startswith("approve_"):

        msg_id = data.replace(
            "approve_",
            ""
        )

        product = pending_products.get(msg_id)

        if not product:
            await query.message.reply_text(
                "Produto expirado."
            )
            return

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🛒 Comprar agora",
                    url=product["link"]
                )
            ]
        ])

        caption = format_message(product)

        try:

            # ENVIA PRO GRUPO
            if product["image"]:

                await context.bot.send_photo(
                    chat_id=GROUP_ID,
                    photo=product["image"],
                    caption=caption,
                    reply_markup=keyboard
                )

            else:

                await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=caption,
                    reply_markup=keyboard
                )

            await query.message.reply_text(
                "✅ Oferta enviada para o grupo!"
            )

        except Exception as e:

            print("ERRO AO ENVIAR:", e)

            await query.message.reply_text(
                f"Erro:\n{e}"
            )

    # =====================
    # RECUSAR
    # =====================

    elif data.startswith("reject_"):

        await query.message.reply_text(
            "❌ Oferta recusada."
        )

# =========================
# START BOT
# =========================

app = Application.builder().token(TOKEN).build()

# RECEBER LINKS
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
)

# BOTÕES
app.add_handler(
    CallbackQueryHandler(buttons)
)

# =========================
# ONLINE
# =========================

if __name__ == "__main__":

    print("BOT ONLINE...")

    app.run_polling(
        poll_interval=2,
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )
