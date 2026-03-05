import re
import asyncio
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# --- 1. AYARLAR ---
TELEGRAM_TOKEN = "8637130007:AAHwNRSwfjZQcfYDoGNKWjuIiBYB8at8fvI"

# Admin Listesi
ADMIN_IDS = [8416720490, 8382929624, 652932220, 7094870780]

# Başlangıç Kara Listesi (ID: İsim)
BLACKLIST = {
    5177820294: "Octopus Game TR",
    1858358799: "Bilinmeyen Bot 1",
    7818025361: "Bilinmeyen Bot 2"
}

BANNED_KEYWORDS = [
    "kanalımıza", "kanalına", "grubuna", "grubumuza", "davetlisiniz"
]

# --- 2. REKLAM ENGELLEME MANTIĞI (GRUPLAR İÇİN) ---

async def delete_octopus_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    
    # Özel mesajları bu fonksiyonda işlemeyelim, sadece gruplar
    if not msg or not user or update.effective_chat.type == 'private':
        return
        
    if user.id in BLACKLIST:
        text = (msg.text or msg.caption or "").lower()
        has_link = bool(re.search(r'(?:https?://)?t\.me/\S+', text))
        has_keyword = any(keyword in text for keyword in BANNED_KEYWORDS)

        if has_link or has_keyword:
            try:
                await msg.delete()
            except Exception as e:
                print(f"Silme hatası: {e}")

# --- 3. ADMİN YÖNETİM SİSTEMİ (ÖZEL MESAJLAR İÇİN) ---

async def unauthorized_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin olmayan biri bota özelden yazarsa uyarır."""
    if update.effective_chat.type == 'private' and update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Bu bot üzerinde herhangi bir yetkin bulunmuyor. Erişim reddedildi.")
        return

async def komutlar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adminlere bot kullanımını anlatır."""
    if update.effective_user.id not in ADMIN_IDS: return
    
    rehber = (
        "🛡 ZENITHAR ANTI-AD BOT KOMUTLARI\n\n"
        "🔹 /engelle BOT_ID` : reklam atan bir hesabı ya da botu kara listeye ekler.\n"
        "🔹 /liste` : Şu anki kara listeyi sıralı şekilde getşrir.\n"
        "🔹 /izinver SIRA_NO` : Listeden birini çıkarmak için sıra numarasını yaz.\n"
    )
    await update.message.reply_text(rehber, parse_mode="Markdown")

async def engelle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
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
        await update.message.reply_text("❌ Geçersiz ID formatı.")

async def liste_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not BLACKLIST:
        await update.message.reply_text("📭 Kara liste şu an tertemiz.")
        return

    res = "🚫 **AKTİF KARA LİSTE**\n\n"
    for i, (b_id, name) in enumerate(BLACKLIST.items(), 1):
        res += f"{i}. {name} - `{b_id}`\n"
    await update.message.reply_text(res, parse_mode="Markdown")

async def izinver_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args:
        await update.message.reply_text("❌ Kullanım: `/izinver 1`", parse_mode="Markdown")
        return

    try:
        rank = int(context.args[0])
        keys = list(BLACKLIST.keys())
        if 0 < rank <= len(keys):
            target_id = keys[rank - 1]
            removed_name = BLACKLIST.pop(target_id)
            await update.message.reply_text(f"🔓 **{removed_name}** affedildi, listeden çıkarıldı.", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Liste numarasını yanlış girdin.")
    except ValueError:
        await update.message.reply_text("❌ Lütfen sadece sayı gir.")

# --- 4. ANA ÇALIŞTIRICI ---

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Komutlar
    app.add_handler(CommandHandler("komutlar", komutlar_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("engelle", engelle_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("liste", liste_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("izinver", izinver_command, filters=filters.ChatType.PRIVATE))
    
    # Özel mesajda admin olmayanları yakalayan handler (Komut olmayan her şey için)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & (~filters.COMMAND), unauthorized_check))
    
    # Gruplarda reklam silen handler
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.ALL, delete_octopus_ads))
    
    print("Anti-Reklam Sistemi v2.1 Yayında. Adminler yetkilendirildi.")
    app.run_polling()

if __name__ == "__main__":
    main()
