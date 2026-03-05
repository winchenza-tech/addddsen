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

BANNED_KEYWORDS = [
    "kanalımıza", "kanalına", "grubuna", "grubumuza", "davetlisiniz"
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
        text = (msg.text or msg.caption or "").lower()
        has_link = bool(re.search(r'(?:https?://)?t\.me/\S+', text))
        has_keyword = any(keyword in text for keyword in BANNED_KEYWORDS)

        if has_link or has_keyword:
            try:
                await msg.delete()
            except:
                pass

# --- 4. ADMİN YÖNETİM SİSTEMİ (ÖZEL MESAJLAR İÇİN) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Botun ilk etkileşimini yönetir."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Bu bot üzerinde herhangi bir yetkin bulunmuyor. Erişim reddedildi.")
        return
    
    await update.message.reply_text(
        "🖐 Selam Zenithar ve ekibi! Reklam avcısı sistemine hoş geldiniz.\n"
        "Komutları görmek için `/komutlar` yazabilirsiniz.",
        parse_mode="Markdown"
    )

async def komutlar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rehber mesajı."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Yetkisiz erişim.")
        return
    
    rehber = (
        "🛡 ZenithAD Blocker kullanım rehberi:\n\n"
        "🔹 `/engelle BOT_ID` : Yeni bir botu kara listeye ekler.\n"
        "🔹 `/liste` : Mevcut kara listeyi sıralı gösterşr.\n"
        "🔹 `/izinver SIRA_NO` : Listeden bir botu çıkartır.\n"
    )
    await update.message.reply_text(rehber, parse_mode="Markdown")

async def engelle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("❌ Kullanım: `/engelle 123456789`", parse_mode="Markdown")
        return

    try:
        new_id = int(context.args[0])
        try:
            bot_chat = await context.bot.get_chat(new_id)
            bot_name = bot_chat.first_name or bot_chat.title
        except:
            bot_name = f"Bilinmeyen Bot ({new_id})"

        BLACKLIST[new_id] = bot_name
        await update.message.reply_text(f"✅ {bot_name} kara listeye eklendi.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Geçersiz ID. Sadece sayı girin.")

async def liste_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not BLACKLIST:
        await update.message.reply_text("📭 Kara liste boş.")
        return

    res = "🚫 **KARA LİSTE**\n\n"
    for i, (b_id, name) in enumerate(BLACKLIST.items(), 1):
        res += f"{i}. {name} - `{b_id}`\n"
    await update.message.reply_text(res, parse_mode="Markdown")

async def izinver_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("❌ Kullanım: `/izinver 1`", parse_mode="Markdown")
        return

    try:
        rank = int(context.args[0])
        keys = list(BLACKLIST.keys())
        if 0 < rank <= len(keys):
            target_id = keys[rank - 1]
            removed_name = BLACKLIST.pop(target_id)
            await update.message.reply_text(f"🔓 **{removed_name}** listeden çıkartıldı.", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Geçersiz sıra numarası.")
    except ValueError:
        await update.message.reply_text("❌ Sayı girin.")

async def catch_unauthorized_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin olmayanların attığı her türlü mesajı (özelde) yakalar."""
    if update.effective_chat.type == 'private' and not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Bu bot üzerinde herhangi bir yetkin bulunmuyor. Erişim reddedildi.")

# --- 5. ANA ÇALIŞTIRICI ---

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # 1. Öncelik: /start ve /komutlar (Admin kontrolü içlerinde yapılıyor)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("komutlar", komutlar_command))
    app.add_handler(CommandHandler("engelle", engelle_command))
    app.add_handler(CommandHandler("liste", liste_command))
    app.add_handler(CommandHandler("izinver", izinver_command))
    
    # 2. Öncelik: Özel mesajda admin olmayanların HER ŞEYİNİ yakala (Komut dahil)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE, catch_unauthorized_messages), group=1)
    
    # 3. Öncelik: Gruplarda reklam silme
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.ALL, delete_octopus_ads), group=2)
    
    print("Reklam Avcısı v2.2 Çalışıyor. Admin kontrolü sıkılaştırıldı.")
    app.run_polling()

if __name__ == "__main__":
    main()
