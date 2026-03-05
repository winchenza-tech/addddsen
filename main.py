import re
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TELEGRAM_TOKEN = "8637130007:AAHwNRSwfjZQcfYDoGNKWjuIiBYB8at8fvI"
# Artık birden fazla ID'yi hedef alabiliyoruz
TARGET_BOT_IDS = [5177820294, 1858358799, 7818025361, 7818025361] 
BANNED_KEYWORDS = [
    "kanalımıza", "kanalına", "grubuna", "grubumuza", "davetlisiniz"
]

async def delete_octopus_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    
    if not msg or not user:
        return
        
    # Kullanıcı ID'si hedef listemizin içinde mi diye kontrol ediyoruz
    if user.id in TARGET_BOT_IDS:
        text = msg.text or msg.caption or ""
        text_lower = text.lower()
 
        # https://, http:// olsa da olmasa da tüm t.me/ linklerini yakalar
        has_link = bool(re.search(r'(?:https?://)?t\.me/\S+', text_lower))
 
        has_keyword = any(keyword in text_lower for keyword in BANNED_KEYWORDS)

        if has_link or has_keyword:
            try:
                await msg.delete()
                print(f"Geçici test mesajı: {user.id} ID'li hedeften gelen reklam engellendi.")
            except Exception as e:
                print(f"Mesaj silinemedi (Botun grupta admin yetkisi eksik olabilir): {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.ALL, delete_octopus_ads))
    
    print("Anti-Reklam Botu çalışıyor... Hedefler kilitlendi.")
    app.run_polling()

if __name__ == "__main__":
    main()
