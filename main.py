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

TOKEN = ":8993898662:AAFEPMd414DDI767a71F65MT3wqutBaVMH4"
GROUP_ID = -1003761262254
ADMIN_ID = 7198780258

# =========================
# PEGAR IMAGEM
# =========================

def get_image(soup):

    img = soup.find("meta", property="og:image")

    if img and img.get("content"):
        return img["content"]

    return None

# =========================
# PEGAR PREÇO
# =========================

def extract_price(soup):

    text = soup.get_text()

    patterns = [
        r"R\$\s?\d+[.,]?\d*",
        r"\d+[.,]\d{2}"
    ]

    for p in patterns:

        match = re.search(p, text)

        if match:
            return match.group()

    return "Preço não encontrado"

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
            timeout=10
        )

        soup = BeautifulSoup(r.text, "html.parser")

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
                else "Produto"
            )

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
# FORMATAR MSG
# =========================

def format_message(p):

    return f"""
🔥 OFERTA ENCONTRADA 🔥

📦 {p['title']}

💰 {p['price']}

🛒 Link da oferta abaixo
"""

# =========================
# MENSAGEM
# =========================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    # =========================
    # PREÇO MANUAL
    # =========================

    if context.user_data.get("waiting_manual_price"):

        context.user_data["waiting_manual_price"] = False

        product = context.user_data.get(
            "pending_product"
        )

        if not product:

            await update.message.reply_text(
                "Nenhum produto pendente."
            )

            return

        product["price"] = f"R$ {update.message.text}"

        context.user_data["pending_product"] = product

        text = format_message(product)

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Aprovar",
                    callback_data=f"approve|{product['link']}"
                ),

                InlineKeyboardButton(
                    "❌ Recusar",
                    callback_data="reject"
                )
            ]
        ])

        if product["image"]:

            await update.message.reply_photo(
                photo=product["image"],
                caption=text,
                reply_markup=keyboard
            )

        else:

            await update.message.reply_text(
                text,
                reply_markup=keyboard
            )

        return

    # =========================
    # LINK
    # =========================

    if update.message.text:

        url = update.message.text

        if "http" not in url:

            await update.message.reply_text(
                "Envie um link válido."
            )

            return

        product = scrape_product(url)

        context.user_data["pending_product"] = product

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
            ],

            [
                InlineKeyboardButton(
                    "💰 Editar preço",
                    callback_data="manual_price"
                )
            ]
        ])

        if product["image"]:

            await update.message.reply_photo(
                photo=product["image"],
                caption=text,
                reply_markup=keyboard
            )

        else:

            await update.message.reply_text(
                text,
                reply_markup=keyboard
            )

# =========================
# BOTÕES
# =========================

async def button_click(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data

    # =========================
    # APROVAR
    # =========================

    if data.startswith("approve"):

        product = context.user_data.get(
            "pending_product"
        )

        if not product:

            await query.message.reply_text(
                "Produto não encontrado."
            )

            return

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

            await query.edit_message_caption(
                caption="✅ Oferta enviada pro grupo."
            )

        except Exception as e:

            print(e)

            try:

                await query.edit_message_caption(
                    caption=f"❌ Erro:\n{e}"
                )

            except:

                await query.edit_message_text(
                    f"❌ Erro:\n{e}"
                )

    # =========================
    # RECUSAR
    # =========================

    elif data == "reject":

        try:

            await query.edit_message_caption(
                caption="❌ Oferta recusada."
            )

        except:

            await query.edit_message_text(
                "❌ Oferta recusada."
            )

    # =========================
    # EDITAR PREÇO
    # =========================

    elif data == "manual_price":

        context.user_data[
            "waiting_manual_price"
        ] = True

        await query.message.reply_text(
            "Envie o novo preço.\n\nExemplo:\n129,90"
        )

# =========================
# START
# =========================

app = Application.builder().token(TOKEN).build()

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
)

app.add_handler(
    CallbackQueryHandler(button_click)
)

print("BOT ONLINE")

app.run_polling(
    drop_pending_updates=True
        )
