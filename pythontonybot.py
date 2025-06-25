import logging
import os
from PIL import Image
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# === API KEYS ===
TELEGRAM_TOKEN = "8087188419:AAGbEFhigw3MqhnwSx5HTyfR6AEUvh00NPw"
GEMINI_API_KEY = "AIzaSyARIRKeCL3UQRGsiGyIn-OzvYWziSJB-zo"

# === Configure Gemini ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')  # Gemini 1.5 Flash

# === Logging ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# === Mode States ===
USER_MODE = {}
USER_IMAGES = {}

# === Start Command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ Hello! I'm your Gemini 1.5 Flash bot. Use /mode to choose an action.")

# === Mode Selection ===
async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖼️ JPG to PDF", callback_data='mode_jpg')],
        [InlineKeyboardButton("✂️ Split PDF", callback_data='mode_split')],
        [InlineKeyboardButton("📎 Merge PDFs", callback_data='mode_merge')],
        [InlineKeyboardButton("🗜️ Compress PDF", callback_data='mode_compress')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔧 Choose what you want to do:", reply_markup=reply_markup)

# === Handle Mode Selection Callback ===
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

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

# === Handle Photo Upload ===
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

# === Convert Images to PDF ===
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

# === Handle Text with Gemini ===
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        response = model.generate_content(user_input)
        reply = response.text.strip() if hasattr(response, "text") else "🤖 Sorry, I couldn’t generate a response."
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"Gemini error: {e}")
        await update.message.reply_text("⚠️ Gemini API Error.")

# === Main Runner ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mode", mode))
    app.add_handler(CommandHandler("convert", convert))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🚀 Gemini PDF Bot running...")
    app.run_polling()

if __name__ == '__main__':
    main()
