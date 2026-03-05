import re
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Ayarlar
TELEGRAM_TOKEN = "BURAYA_YENI_BOTUNUN_TOKENINI_YAZ"
TARGET_BOT_ID = 5177820294

# Yasaklı kelimeler listesi
BANNED_KEYWORDS = [
    "kanalımıza", "kanalına", "grubuna", "grubumuza", "davetlisiniz"
]

async def delete_octopus_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    
    if not msg or not user:
        return
        
    if user.id == TARGET_BOT_ID:
        text = (msg.text or msg.caption or "").lower()
        
        has_link = bool(re.search(r't\.me/\S+', text))
        has_keyword = any(keyword in text for keyword in BANNED_KEYWORDS)
        
        if has_link or has_keyword:
            try:
                await msg.delete()
            except:
                pass

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, delete_octopus_ads))
    app.run_polling()

if __name__ == "__main__":
    main()