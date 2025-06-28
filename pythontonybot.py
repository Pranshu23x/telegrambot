import logging
import os
import threading
from flask import Flask
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, MessageHandler, CallbackQueryHandler, filters
)

# === Load .env ===
load_dotenv()

# === Secure API KEYS ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# === Configure Gemini ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')

# === Flask App to keep alive ===
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "✅ Bot is running!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# === Logging ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# === Mode States ===
USER_MODE = {}
USER_IMAGES = {}

# === Handlers ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧠 Just Chat", callback_data='just_chat')],
        [InlineKeyboardButton("🖼️ Convert JPG to PDF", callback_data='mode_jpg')],
        [InlineKeyboardButton("✂️ Split PDF", callback_data='mode_split')],
        [InlineKeyboardButton("📎 Merge PDFs", callback_data='mode_merge')],
        [InlineKeyboardButton("🗜️ Compress PDF", callback_data='mode_compress')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Hi there, This is NExt_23x\n, Made by Pranshu\n"
        "I can:\n"
        "🖼️ Convert JPGs to PDFs\n"
        "✂️ Split PDFs into parts\n"
        "📎 Merge multiple PDFs\n"
        "🗜️ Compress large PDF files\n"
        "DO CONNECT ON LINKEDIN:\n"
        "https://www.linkedin.com/in/pranshu-23x?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app",
        reply_markup=reply_markup
    )

async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖼️ JPG to PDF", callback_data='mode_jpg')],
        [InlineKeyboardButton("✂️ Split PDF", callback_data='mode_split')],
        [InlineKeyboardButton("📎 Merge PDFs", callback_data='mode_merge')],
        [InlineKeyboardButton("🗜️ Compress PDF", callback_data='mode_compress')],
        [InlineKeyboardButton("🧠 Just Chat", callback_data='just_chat')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔧 Choose what you want to do:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    if query.data == 'just_chat':
        USER_MODE[chat_id] = 'chat'
        await query.edit_message_text("🧠 You’re now in *Just Chat* mode. Type anything to start chatting with Gemini.", parse_mode="Markdown")
        return

    if query.data == 'mode_jpg':
        USER_MODE[chat_id] = 'jpg_to_pdf_choice'
        keyboard = [
            [InlineKeyboardButton("🗂️ Single PDF", callback_data='jpg_single')],
            [InlineKeyboardButton("📄 Separate PDFs", callback_data='jpg_multiple')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🖼️ Choose JPG to PDF output mode:", reply_markup=reply_markup)

    elif query.data == 'mode_split':
        USER_MODE[chat_id] = 'split_pdf'
        await query.edit_message_text("✂️ Send a PDF and specify pages to split.")

    elif query.data == 'mode_merge':
        USER_MODE[chat_id] = 'merge_pdf'
        USER_IMAGES[chat_id] = []
        await query.edit_message_text("📎 Send all PDFs you want to merge.")

    elif query.data == 'mode_compress':
        USER_MODE[chat_id] = 'compress_pdf'
        await query.edit_message_text("🗜️ Send a PDF to compress.")

    elif query.data in ['jpg_single', 'jpg_multiple']:
        USER_MODE[chat_id] = query.data
        USER_IMAGES[chat_id] = []
        await query.edit_message_text("📤 Now send JPG images.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mode = USER_MODE.get(chat_id)

    if mode not in ['jpg_single', 'jpg_multiple']:
        await update.message.reply_text("❗Please choose JPG to PDF mode first using /mode.")
        return

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_path = f"img_{chat_id}_{len(USER_IMAGES.get(chat_id, []))}.jpg"
    await file.download_to_drive(image_path)
    USER_IMAGES.setdefault(chat_id, []).append(image_path)

    await update.message.reply_text("✅ Image received. Send more or type /convert to generate the PDF.")

async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mode = USER_MODE.get(chat_id)
    images = USER_IMAGES.get(chat_id, [])

    if not images:
        await update.message.reply_text("⚠️ No images uploaded.")
        return

    try:
        if mode == 'jpg_single':
            img_objs = [Image.open(p).convert("RGB") for p in images]
            img_objs[0].save("output.pdf", save_all=True, append_images=img_objs[1:])
            await update.message.reply_document(open("output.pdf", "rb"), filename="merged.pdf")
            os.remove("output.pdf")

        elif mode == 'jpg_multiple':
            for i, path in enumerate(images):
                pdf_path = f"output_{i+1}.pdf"
                Image.open(path).convert("RGB").save(pdf_path)
                await update.message.reply_document(open(pdf_path, "rb"), filename=pdf_path)
                os.remove(pdf_path)

    except Exception as e:
        logging.error(f"Convert error: {e}")
        await update.message.reply_text("❌ Failed to convert JPGs to PDF.")

    for p in images:
        if os.path.exists(p):
            os.remove(p)

    USER_IMAGES[chat_id] = []
    USER_MODE[chat_id] = None

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mode = USER_MODE.get(chat_id)

    if mode != 'chat':
        await update.message.reply_text("💬 Please select *Just Chat* from /start to begin chatting with Gemini.", parse_mode="Markdown")
        return

    user_input = update.message.text
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        response = model.generate_content(user_input)
        reply = response.text.strip() if hasattr(response, "text") else "🤖 Sorry, I couldn’t generate a response."
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"Gemini error: {e}")
        await update.message.reply_text("⚠️ Gemini API Error.")

# === Main Runner ===

def run_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mode", mode))
    app.add_handler(CommandHandler("convert", convert))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logging.info("🚀 Gemini PDF Bot polling...")
    app.run_polling()

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    run_bot()