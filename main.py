    import requests
from bs4 import BeautifulSoup
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, CallbackContext


# =========================
# CONFIG
# =========================
TOKEN = "8993898662:AAEThBQVbytvrVfgQayffhAyUUxlfIdlfMs"
GROUP_ID = 5113725387


# =========================
# DADOS TEMPORÁRIOS
# =========================
pending_offers = {}
offer_id = 0


# =========================
# SCRAPER
# =========================
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
            title = soup.title.string.strip() if soup.title else "Sem título"

        # IMAGEM
        img = soup.find("meta", property="og:image")
        image = img["content"] if img else None

        # PREÇO (fallback simples)
        price_match = re.search(r"R\$\s?\d+[.,]?\d*", soup.get_text())
        price = price_match.group() if price_match else "Ver no link"

        return {
            "title": title,
            "price": price,
            "image": image,
            "link": url
        }

    except Exception as e:
        print("SCRAPER ERROR:", e)
        return {
            "title": "Erro ao carregar produto",
            "price": "Ver no link",
            "image": None,
            "link": url
        }


# =========================
# FORMATAÇÃO FINAL
# =========================
def format_offer(p):
    return f"""
🔥 OFERTA PUBLICADA 🔥

📦 {p['title']}
💰 {p['price']}

🛒 Link: {p['link']}
"""


# =========================
# MENSAGEM RECEBIDA
# =========================
def handle(update: Update, context: CallbackContext):
    global offer_id

    url = update.message.text

    if "http" not in url:
        update.message.reply_text("❌ Envie um link válido.")
        return

    product = scrape_product(url)

    offer_id += 1
    current_id = str(offer_id)

    pending_offers[current_id] = product

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Aceitar", callback_data=f"accept_{current_id}"),
            InlineKeyboardButton("✏️ Editar", callback_data=f"edit_{current_id}"),
            InlineKeyboardButton("❌ Recusar", callback_data=f"reject_{current_id}")
        ]
    ])

    text = f"""
🧪 PRÉVIA DE OFERTA

📦 {product['title']}
💰 {product['price']}
"""

    if product["image"]:
        update.message.reply_photo(
            photo=product["image"],
            caption=text,
            reply_markup=keyboard
        )
    else:
        update.message.reply_text(text, reply_markup=keyboard)


# =========================
# BOTÕES (CORRIGIDO)
# =========================
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    data = query.data

    print("CALLBACK RECEBIDO:", data)  # DEBUG

    if "_" not in data:
        query.edit_message_text("❌ Erro no botão.")
        return

    action, id_ = data.split("_")

    product = pending_offers.get(id_)

    if not product:
        query.edit_message_text("⚠️ Oferta expirada.")
        return

    # =========================
    # ACEITAR
    # =========================
    if action == "accept":
        msg = format_offer(product)

        try:
            context.bot.send_message(
                chat_id=GROUP_ID,
                text=msg
            )

            query.edit_message_text("✅ Publicado no grupo!")

        except Exception as e:
            print("ERRO AO ENVIAR NO GRUPO:", e)
            query.edit_message_text("❌ Erro ao enviar no grupo")

    # =========================
    # RECUSAR
    # =========================
    elif action == "reject":
        query.edit_message_text("❌ Oferta recusada")

    # =========================
    # EDITAR (ainda básico)
    # =========================
    elif action == "edit":
        query.edit_message_text("✏️ Edição ainda não implementada")


# =========================
# START BOT
# =========================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))
    dp.add_handler(CallbackQueryHandler(button))

    print("🤖 Bot rodando...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
