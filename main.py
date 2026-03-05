import re
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# --- AYARLAR ---
TELEGRAM_TOKEN = "8637130007:AAHwNRSwfjZQcfYDoGNKWjuIiBYB8at8fvI"

# Admin Listesi
ADMIN_IDS = [8416720490, 8382929624, 652932220, 7094870780]

# Başlangıç Kara Listesi (ID: İsim şeklinde tutuyoruz)
# Not: Railway gibi platformlarda bot yeniden başlarsa bu liste bu hale döner.
BLACKLIST = {
    5177820294: "Octopus Game TR",
    1858358799: "Bilinmeyen Bot 1",
    7818025361: "Bilinmeyen Bot 2"
}

BANNED_KEYWORDS = [
    "kanalımıza", "kanalına", "grubuna", "grubumuza", "davetlisiniz"
]

# --- REKLAM ENGELLEME MANTIĞI ---

async def delete_octopus_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    
    if not msg or not user:
        return
        
    # Kullanıcı ID'si kara listede mi?
    if user.id in BLACKLIST:
        text = msg.text or msg.caption or ""
        text_lower = text.lower()
 
        # t.me linklerini yakalar
        has_link = bool(re.search(r'(?:https?://)?t\.me/\S+', text_lower))
        has_keyword = any(keyword in text_lower for keyword in BANNED_KEYWORDS)

        if has_link or has_keyword:
            try:
                await msg.delete()
                print(f"Engellendi: {BLACKLIST[user.id]} ({user.id})")
            except Exception as e:
                print(f"Silme hatası: {e}")

# --- ADMİN KOMUTLARI ---

async def engelle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args:
        await update.message.reply_text("Kullanım: /engelle bot_id")
        return

    try:
        new_id = int(context.args[0])
        # Bot ismini çekmeye çalışalım
        try:
            bot_chat = await context.bot.get_chat(new_id)
            bot_name = bot_chat.first_name or bot_chat.title
        except:
            bot_name = f"ID: {new_id}"

        BLACKLIST[new_id] = bot_name
        await update.message.reply_text(f"✅ {bot_name} ({new_id}) kara listeye eklendi.")
    except ValueError:
        await update.message.reply_text("❌ Lütfen geçerli bir sayısal ID girin.")

async def liste_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    
    if not BLACKLIST:
        await update.message.reply_text("Kara liste şu an boş.")
        return

    res = "🚫 **KARA LİSTE (BLACKLIST)**\n\n"
    for i, (b_id, name) in enumerate(BLACKLIST.items(), 1):
        res += f"{i}. {name} - `{b_id}`\n"
    
    await update.message.reply_text(res, parse_mode="Markdown")

async def izinver_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args:
        await update.message.reply_text("Kullanım: /izinver sıra_no")
        return

    try:
        rank = int(context.args[0])
        # Dict'ten index ile öğe çekme
        keys = list(BLACKLIST.keys())
        if 0 < rank <= len(keys):
            target_id = keys[rank - 1]
            removed_name = BLACKLIST.pop(target_id)
            await update.message.reply_text(f"🔓 {removed_name} listeden çıkarıldı. Artık özgür.")
        else:
            await update.message.reply_text("❌ Geçersiz sıra numarası. Listeyi /liste ile kontrol et.")
    except ValueError:
        await update.message.reply_text("❌ Lütfen bir sayı girin.")

# --- ANA ÇALIŞTIRICI ---

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Komutlar (Sadece özel mesajda çalışması için filtre eklenebilir ama admin kontrolü zaten var)
    app.add_handler(CommandHandler("engelle", engelle_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("liste", liste_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("izinver", izinver_command, filters=filters.ChatType.PRIVATE))
    
    # Tüm mesajları dinleyen reklam engelleyici
    app.add_handler(MessageHandler(filters.ALL, delete_octopus_ads))
    
    print("Reklam Avcısı v2 Aktif! Adminler görev başında.")
    app.run_polling()

if __name__ == "__main__":
    main()
