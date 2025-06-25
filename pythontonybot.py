Python 3.12.9 (tags/v3.12.9:fdb8142, Feb  4 2025, 15:27:58) [MSC v.1942 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license()" for more information.
>>> import logging
... import openai
... from telegram import Update, ChatAction
... from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
... 
... # === Securely Set Your API Keys (in quotes) ===
... TELEGRAM_TOKEN = "8087188419:AAGbEFhigw3MqhnwSx5HTyfR6AEUvh00NPw"
... OPENAI_API_KEY = "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"
... 
... openai.api_key = OPENAI_API_KEY
... 
... # === Logging ===
... logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
... 
... # === Start Command ===
... async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
...     await update.message.reply_text("🤖 Hello! I'm your OpenAI-powered chatbot. Ask me anything!")
... 
... # === Message Handler ===
... async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
...     user_input = update.message.text
... 
...     # Show typing animation
...     await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
... 
...     try:
...         # OpenAI response
...         response = openai.ChatCompletion.create(
...             model="gpt-3.5-turbo",
...             messages=[
...                 {"role": "system", "content": "You are a helpful and clever assistant."},
...                 {"role": "user", "content": user_input}
...             ],
...             temperature=0.7,
...             max_tokens=300
...         )
... 
...         reply = response['choices'][0]['message']['content'].strip()
...         await update.message.reply_text(reply)
... 
...     except Exception as e:
...         logging.error(e)
...         await update.message.reply_text("⚠️ Sorry, something went wrong while processing your request.")
... 
# === Main Runner ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
