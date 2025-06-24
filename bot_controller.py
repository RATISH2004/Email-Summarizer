import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TG_BOT_TOKEN")
API_URL = "http://127.0.0.1:5000/api/emails"
WEB_URL = "http://127.0.0.1:5000"

def format_email_message(emails, level):
    output = ""
    for email in emails:
        importance = email.get("categories", [None])[0]
        if importance and importance.lower() == level.lower():
            subject = email.get("subject", "No subject")
            sender = email.get("from", "Unknown sender")
            output += f"📧 Subject: {subject}\n👤 From: {sender}\n\n"
    return output if output else "None found.\n"

def get_emails_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return response.json().get("emails", [])
    except Exception as e:
        print(f"Error fetching emails: {e}")
    return []

# --------- Async Handlers ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📬 Welcome to your Email Summary Bot!\n\nUse /get_emails to get today's prioritized email summary.\nUse /open to open the website."
    )

async def get_emails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emails = get_emails_data()
    if not emails:
        await update.message.reply_text("⚠ No emails found or unable to fetch from server.")
        return

    very_important = format_email_message(emails, "Very Important")
    important = format_email_message(emails, "Important")
    Unimportant = format_email_message(emails, "Unimportant")

    await update.message.reply_text("📌 Very Important Emails:\n" + very_important, parse_mode='Markdown')
    await update.message.reply_text("📌 Important Emails:\n" + important, parse_mode='Markdown')
    await update.message.reply_text("📌 Unimportant Emails:\n" + Unimportant, parse_mode='Markdown')
    await update.message.reply_text(f"🌐 Open the full email dashboard here: {WEB_URL}")

async def open_website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🌐 Open the full email dashboard here: {WEB_URL}")

# --------- Entry Point ---------
def main():
    if not TELEGRAM_TOKEN:
        print("❌ Telegram token not found in .env")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_emails", get_emails))
    app.add_handler(CommandHandler("open", open_website))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()