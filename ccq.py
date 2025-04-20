import random
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# NEW IMPORTS
import os
from dotenv import load_dotenv
import stripe
stripe.api_key = "sk_test_51RFoFwQ08BSBpCMxsqQbX5fvfrEQU2W1m08bi95Z1Z0cuozwKeqtTVluzfG9uSuotGmtpt12ndkd1QDy9fJesmqp00ghDUotxw"  # Yaha apna Stripe secret test key dlo

def stripe_check_card(cc, mm, yy, cvv):
    try:
        token = stripe.Token.create(
            card={
                "number": cc,
                "exp_month": int(mm),
                "exp_year": int(f"20{yy}"),
                "cvc": cvv,
            },
        )
        return {"status": "Approved ✅", "response": "Token created", "token_id": token.id}
    except stripe.error.CardError as e:
        return {"status": "Declined ❌", "response": str(e.user_message)}
    except Exception as e:
        return {"status": "Declined ❌", "response": str(e)}
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 1. /gen command – Card generator
async def gen_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        bin_format = context.args[0]
        if len(bin_format) != 6 or not bin_format.isdigit():
            await update.message.reply_text("Usage: /gen <6-digit BIN>")
            return

        # BIN Lookup
        r = requests.get(f"https://lookup.binlist.net/{bin_format}")
print("DEBUG API Response:", r.status_code, r.text)  # debugging

if r.status_code != 200:
    await update.message.reply_text("Invalid BIN or BIN lookup failed.")
    return

data = r.json()

brand = data.get("scheme", "UNKNOWN").upper()
card_type = data.get("type", "UNKNOWN").upper()
country_info = data.get("country", {})
country = country_info.get("name", "UNKNOWN")
emoji = country_info.get("emoji", "")
        user = update.effective_user
        username = user.username or user.first_name
        generation_time = round(random.uniform(1.5, 3.5), 2)

        generated_cards = []
        for _ in range(10):
            cc = bin_format + ''.join(random.choices('0123456789', k=10))
            mm = str(random.randint(1, 12)).zfill(2)
            yy = str(random.randint(25, 30))
            cvv = ''.join(random.choices('0123456789', k=3))
            generated_cards.append(f"{cc}|{mm}|{yy}|{cvv}")

        message = f"""
CC Generated Successfully
------------------------------
Amount ➜ 10

{"\n".join(generated_cards)}

Info ➜ {brand} - {card_type} - STANDARD PREPAID GENERAL SPEND
Bank ➜ {user.first_name} LIMITED
Country ➜ {country} {emoji}
Time ➜ {generation_time} seconds
Checked By ➜ {username}
[ FREE ]
"""
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text("Error generating cards.")

# 2. .chk command – BIN checker with simulated Approved/Declined result
async def chk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message.text
        if not message.startswith(".chk"):
            return

        parts = message.split()
        if len(parts) != 2:
            await update.message.reply_text("Usage: .chk <cc|mm|yy|cvv>")
            return

        cc_details = parts[1].split("|")
        if len(cc_details) != 4:
            await update.message.reply_text("Invalid card format.")
            return

        cc, mm, yy, cvv = cc_details
        user = update.effective_user
        username = user.username or user.first_name

        result = stripe_check_card(cc, mm, yy, cvv)

        msg = f"""
CC: {cc}|{mm}|20{yy}|{cvv}
Status: {result['status']}
Response: {result['response']}
Gateway: Stripe
Checked by: {username}
"""
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")
    
# 3. /bin command – Full BIN lookup
async def bin_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if not args or not args[0].isdigit() or len(args[0]) < 6:
            await update.message.reply_text("Usage: /bin <6-digit BIN>")
            return

        bin_number = args[0]
        user = update.effective_user

        # Try to get BIN data
        r = requests.get(f"https://lookup.binlist.net/{bin_number}")
        
        if r.status_code != 200:
            await update.message.reply_text("BIN not found.")
            return

        data = r.json()

        if "scheme" not in data:
            await update.message.reply_text("No valid BIN data found.")
            return

        brand = data.get("scheme", "Unknown").upper()
        card_type = data.get("type", "Unknown").upper()
        category = "PREPAID" if data.get("prepaid", False) else "DEBIT"
        issuer = data.get("bank", {}).get("name", "Unknown")
        country = data.get("country", {}).get("name", "Unknown")
        emoji = data.get("country", {}).get("emoji", "")

        message = f"""
⊗ Bin: {bin_number}
⊗ Info: {brand} - {card_type} - {category}
⊗ Issuer: {issuer}
⊗ Country: {country} {emoji}

⊗ Checked By ➜ ------{user.first_name.upper()} ☠️
"""
        await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# /start command – Welcome message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "Hey there, welcome to the Bot!\n\n"
        "I'm here to help you generate and check cards.\n"
        "Use /gen to generate cards, .chk to check them, or /bin to look up BIN info.\n\n"
        "Bot Owner: @SIDIKI_MUSTAFA_92"
    )
    await update.message.reply_text(welcome_message)

# /help command – Show all available commands
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Here are the available commands:\n\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "/gen <6-digit BIN> - Generate test cards using a BIN\n"
        ".chk <cc|mm|yy|cvv> - Check card with simulated result\n"
        "/bin <6-digit BIN> - Look up BIN information\n\n"
        "Bot Owner: @SIDIKI_MUSTAFA_92"
    )
    await update.message.reply_text(help_text)

# Bot start
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("gen", gen_cards))
    app.add_handler(CommandHandler("bin", bin_lookup))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^\.chk "), chk_handler))

    print("Bot is running...")
    app.run_polling()ssage\n"
        "/help - Show this help message\n"
        "/gen <6-digit BIN> - Generate test cards using a BIN\n"
        ".chk <cc|mm|yy|cvv> - Check card with simulated result\n"
        "/bin <6-digit BIN> - Look up BIN information\n\n"
        "Bot Owner: @SIDIKI_MUSTAFA_92"
    )
    await update.message.reply_text(help_text)

# Bot start
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("gen", gen_cards))
    app.add_handler(CommandHandler("bin", bin_lookup))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^\.chk "), chk_handler))

    print("Bot is running...")
    app.run_polling()_handler(MessageHandler(filters.TEXT & filters.Regex(r"^\.chk "), chk_handler))

    print("Bot is running...")
    app.run_polling()p))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^\.chk "), chk_handler))

    print("Bot is running...")
    app.run_polling()ot is running...")
    app.run_polling()