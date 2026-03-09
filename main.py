import re
import asyncio
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
    7818025361: "Bilinmeyen Bot 2",
    7495125802: "Test Hesabı"  # <-- Yeni eklediğimiz ID
}

# Yasaklı kelimeler (Küçük harf olarak kontrol edilecek, tekrarlar temizlendi)
BANNED_KEYWORDS = [
    "kanalımıza", "kanalına", "kanal", 
    "grubuna", "grubumuza", 
    "davetlisiniz", "katılabilirsiniz"
]

# --- 2. YARDIMCI FONKSİYONLAR ---
def is_admin(user_id):
    return user_id in ADMIN_IDS

# --- 3. REKLAM ENGELLEME (GRUPLAR İÇİN) ---
async def delete_octopus_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    
    # Sadece gruplardaki mesajları ve geçerli mesajları kontrol et
    if not msg or not user or update.effective_chat.type == 'private':
        return
        
    # Adminlerin mesajlarına dokunma ve kontrolü atla
    if is_admin(user.id):
        return

    # DURUM 1: Kullanıcı kara listedeyse koşulsuz şartsız mesajını sil
    if user.id in BLACKLIST:
        try:
            await msg.delete()
            print(f"Kara Liste Silinmesi: {user.id} ({BLACKLIST[user.id]})")
        except Exception as e:
            print(f"Silme Hatası (Kara Liste): {e}")
        return # İşlemi bitir, metin aramaya gerek kalmadı

    # DURUM 2: Kara listede değilse, metin içeriğini kontrol et
    text = (msg.text or msg.caption or "")
    if not text:
        return

    # Regex ile link arama: t.me/ veya telegram.me/ yakalar
    has_link = bool(re.search(r'(t\.me|telegram\.me)\/', text, re.IGNORECASE))
    
    # Kelime kontrolü için Türkçe karakterleri normalize et ve küçük harfe çevir
    text_lower = text.lower().replace('İ', 'i').replace('I', 'ı')
    
    # Yasaklı kelimelerden herhangi biri metinde geçiyor mu?
    has_keyword = any(keyword in text_lower for keyword in BANNED_KEYWORDS)

    # Eğer link veya yasaklı kelime varsa sil
    if has_link or has_keyword:
        try:
            await msg.delete()
            print(f"Reklam Silindi: {user.id} - İçerik: {text[:30]}...")
        except Exception as e:
            print(f"Silme Hatası (Reklam): {e}")

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
        "🔹 `/engelle ID` : Botu veya kullanıcıyı kara listeye ekler.\n"
        "🔹 `/liste` : Kara listeyi gösterir.\n"
        "🔹 `/izinver SIRA_NO` : Kara listeden çıkarır.\n"
    )
    await update.message.reply_text(rehber, parse_mode="Markdown")

async def engelle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: 
        await update.message.reply_text("Kullanım: `/engelle ID`", parse_mode="Markdown")
        return
        
    try:
        new_id = int(context.args[0])
        try:
            bot_chat = await context.bot.get_chat(new_id)
            bot_name = bot_chat.first_name or bot_chat.title or f"Bilinmeyen ({new_id})"
        except:
            bot_name = f"Bilinmeyen ({new_id})"
            
        BLACKLIST[new_id] = bot_name
        await update.message.reply_text(f"✅ {bot_name} kara listeye eklendi.")
    except ValueError:
        await update.message.reply_text("❌ Geçersiz ID. Lütfen rakamlardan oluşan bir ID girin.")

async def liste_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not BLACKLIST:
        await update.message.reply_text("Kara liste boş.")
        return
        
    res = "🚫 **KARA LİSTE**\n\n"
    for i, (b_id, name) in enumerate(BLACKLIST.items(), 1):
        res += f"{i}. {name} - `{b_id}`\n"
    await update.message.reply_text(res, parse_mode="Markdown")

async def izinver_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: 
        await update.message.reply_text("Kullanım: `/izinver SIRA_NO`", parse_mode="Markdown")
        return
        
    try:
        rank = int(context.args[0])
        keys = list(BLACKLIST.keys())
        if 0 < rank <= len(keys):
            target_id = keys[rank - 1]
            name = BLACKLIST.pop(target_id)
            await update.message.reply_text(f"🔓 {name} kara listeden çıkarıldı.")
        else:
            await update.message.reply_text("❌ Geçersiz sıra numarası. Lütfen `/liste` komutuyla numaraları kontrol edin.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Hata. Lütfen listedeki sıra numarasını girin (Örn: `/izinver 1`).", parse_mode="Markdown")

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
    
    print("Bot aktif. Regex, kelime filtresi ve kara liste sistemi devrede.")
    app.run_polling()

if __name__ == "__main__":
    main()
