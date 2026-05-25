import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8993898662:AAG2cNJoFnJwOYv3tPqxD0mtBOub5cOxtoE"

# -------- SCRAPER --------
def scrape_product(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    # Nome
    title = soup.title.string if soup.title else "Produto"

    # Imagem principal
    image = ""
    img_tag = soup.find("meta", property="og:image")
    if img_tag:
        image = img_tag.get("content")

    # Tenta achar preço no texto (simples)
    text = soup.get_text()
    price = "Não encontrado"

    import re
    match = re.search(r"R\$\s?\d+[\.,]?\d*", text)
    if match:
        price = match.group()

    return {
        "title": title,
        "image": image,
        "price": price,
        "link": url
    }

# -------- FORMATADOR CYBERPUNK --------
def format_message(p):
    return f"""
⚡ REX TECH DEAL ⚡

📦 {p['title']}
💰 {p['price']}
🔥 Oferta automática

━━━━━━━━━━━━━━
🧬 Powered by Rex Tech
"""

# -------- HANDLER TELEGRAM --------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "aliexpress" not in url and "http" not in url:
        await update.message.reply_text("Envie um link válido.")
        return

    product = scrape_product(url)

    caption = format_message(product)

    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Comprar agora", url=product["link"])]
    ])

    if product["image"]:
        await update.message.reply_photo(
            photo=product["image"],
            caption=caption,
            reply_markup=button
        )
    else:
        await update.message.reply_text(caption, reply_markup=button)

# -------- RUN BOT --------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()
