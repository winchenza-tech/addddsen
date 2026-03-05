import re
import asyncio
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# --- 1. AYARLAR ---
TELEGRAM_TOKEN = "8637130007:AAHwNRSwfjZQcfYDoGNKWjuIiBYB8at8fvI"

# Admin Listesi
ADMIN_IDS = [8416720490, 8382929624, 652932220, 7094870780]

# Başlangıç Kara Listesi
BLACKLIST = {
    5177820294: "Octopus Game TR",
    1858358799: "Bilinmeyen Bot 1",
    7818025361: "Bilinmeyen Bot 2"
}

# Yasaklı kelimeler (Küçük harf olarak kontrol edilecek)
# Tüm varyasyonları tek tek eklemek yerine kontrol sırasında metni normalize ediyoruz.
BANNED_KEYWORDS = [
    "kanalımıza", "kanalına", "grubuna", "grubumuza", 
    "davetlisiniz", "davetlisiniz", "davetlisiniz", "davetlisiniz"
]

# --- 2. YARDIMCI FONKSİYONLAR ---

def is_admin(user_id):
    return user_id in ADMIN_IDS

# --- 3. REKLAM ENGELLEME (GRUPLAR İÇİN) ---

async def delete_octopus_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    
    if not msg or not user or update.effective_chat.type == 'private':
        return
        
    if user.id in BLACKLIST:
        # Metni al, hem normal hem de Türkçe karakter uyumu için küçük harfe çevir
        text = (msg.text or msg.caption or "")
        # Regex ile link arama: t.me/ ifadesini metnin neresinde olursa olsun (önünde emoji olsa bile) yakalar
        # Re.IGNORECASE ile büyük/küçük harf duyarlılığını kaldırıyoruz
        has_link = bool(re.search(r't\.me\/', text, re.IGNORECASE))
        
        # Kelime kontrolü için metni normalize et
        text_lower = text.lower().replace('İ', 'i').replace('I', 'ı')
        
        # "davetlisiniz" kelimesinin tüm varyasyonlarını yakalamak için kontrol
        # hem davetlisiniz hem de davetlisiniz (i/ı farkı) taranır
        has_keyword = any(keyword in text_lower for keyword in [
            "davetlisiniz", "davetlisiniz", "kanal", "grubumuza", "grubuna"
        ])

        if has_link or has_keyword:
            try:
                await msg.delete()
                print(f"Reklam Silindi: {user.id} - İçerik: {text[:20]}...")
            except Exception as e:
                print(f"Silme Hatası: {e}")

# --- 4. ADMİN YÖNETİM SİSTEMİ (ÖZEL MESAJLAR İÇİN) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Bu bot üzerinde herhangi bir yetkin bulunmuyor. Erişim reddedildi.")
        return
    await update.message.reply_text("🛡 Hoş geldin admin. Komutlar için `/komutlar` yazabilirsin.")

async def komutlar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    rehber = (
        "🛡 **KOMUT REHBERİ**\n\n"
        "🔹 `/engelle ID` : Botu listeye ekler.\n"
        "🔹 `/liste` : Kara listeyi gösterir.\n"
        "🔹 `/izinver NO` : Botu listeden çıkarır.\n"
    )
    await update.message.reply_text(rehber, parse_mode="Markdown")

async def engelle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    try:
        new_id = int(context.args[0])
        try:
            bot_chat = await context.bot.get_chat(new_id)
            bot_name = bot_chat.first_name or bot_chat.title
        except:
            bot_name = f"Bilinmeyen ({new_id})"
        BLACKLIST[new_id] = bot_name
        await update.message.reply_text(f"✅ {bot_name} eklendi.")
    except:
        await update.message.reply_text("❌ Geçersiz ID.")

async def liste_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not BLACKLIST:
        await update.message.reply_text("Liste boş.")
        return
    res = "🚫 **KARA LİSTE**\n\n"
    for i, (b_id, name) in enumerate(BLACKLIST.items(), 1):
        res += f"{i}. {name} - `{b_id}`\n"
    await update.message.reply_text(res, parse_mode="Markdown")

async def izinver_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    try:
        rank = int(context.args[0])
        keys = list(BLACKLIST.keys())
        if 0 < rank <= len(keys):
            target_id = keys[rank - 1]
            name = BLACKLIST.pop(target_id)
            await update.message.reply_text(f"🔓 {name} çıkarıldı.")
    except:
        await update.message.reply_text("❌ Hata.")

async def catch_unauthorized_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private' and not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Yetkiniz bulunmuyor.")

# --- 5. ANA ÇALIŞTIRICI ---

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("komutlar", komutlar_command))
    app.add_handler(CommandHandler("engelle", engelle_command))
    app.add_handler(CommandHandler("liste", liste_command))
    app.add_handler(CommandHandler("izinver", izinver_command))
    
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE, catch_unauthorized_messages), group=1)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.ALL, delete_octopus_ads), group=2)
    
    print("Bot aktif. Regex ve kelime filtresi güçlendirildi.")
    app.run_polling()

if __name__ == "__main__":
    main()
