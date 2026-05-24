import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ===== SOZLAMALAR =====
BOT_TOKEN = "8950435894:AAEFTuQoHH8pXPntXVPSuMUFCSdUFnRKFGE"
ADMIN_ID = 5825531272

CARDS = {
    "humo": "💚 Humo: 9860 1666 5622 7914\n👤 Abdokimov Z",
    "visa": "💳 Visa: 4231 2000 8075 5357\n👤 Abdokimov Z",
}

PACKAGES = [
    ("30 UC",   "6 000 so'm"),
    ("60 UC",   "11 500 so'm"),
    ("120 UC",  "23 000 so'm"),
    ("180 UC",  "34 500 so'm"),
    ("325 UC",  "57 000 so'm"),
    ("385 UC",  "68 500 so'm"),
    ("445 UC",  "80 000 so'm"),
    ("660 UC",  "114 500 so'm"),
    ("720 UC",  "125 000 so'm"),
    ("985 UC",  "171 500 so'm"),
    ("1800 UC", "277 000 so'm"),
    ("2460 UC", "395 000 so'm"),
    ("3850 UC", "565 500 so'm"),
    ("5650 UC", "846 500 so'm"),
    ("8100 UC", "1 140 000 so'm"),
]

# ConversationHandler states
SELECT_PACKAGE, SELECT_CARD, ENTER_PLAYER_ID, SEND_CHECK = range(4)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== /start =====
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("💎 UC Sotib olish", callback_data="buy")],
          [InlineKeyboardButton("📋 Buyurtmalarim", callback_data="my_orders")],
          [InlineKeyboardButton("📞 Admin bilan bog'lanish", url="https://t.me/RuzoUC")]]
    await update.message.reply_text(
        "🎮 *RuzoUC Bot ga xush kelibsiz!*\n\n"
        "PUBG Mobile uchun UC sotib olishingiz mumkin.\n"
        "⚡ Tez · ✅ Ishonchli · 💰 Arzon",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ===== PAKET TANLASH =====
async def buy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    buttons = []
    for i, (uc, price) in enumerate(PACKAGES):
        buttons.append([InlineKeyboardButton(
            f"💎 {uc} — {price}", callback_data=f"pkg_{i}"
        )])
    buttons.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_start")])

    await query.edit_message_text(
        "💎 *Paket tanlang:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return SELECT_PACKAGE

# ===== PAKET TANLANDI =====
async def package_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = int(query.data.split("_")[1])
    uc, price = PACKAGES[idx]
    ctx.user_data["package"] = f"{uc} — {price}"
    ctx.user_data["pkg_idx"] = idx

    kb = [
        [InlineKeyboardButton("💚 Humo", callback_data="card_humo"),
         InlineKeyboardButton("💳 Visa", callback_data="card_visa")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="buy")]
    ]
    await query.edit_message_text(
        f"✅ Tanlangan: *{uc} — {price}*\n\n"
        "💳 *To'lov usulini tanlang:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return SELECT_CARD

# ===== KARTA TANLANDI =====
async def card_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    card_type = query.data.split("_")[1]
    card_info = CARDS[card_type]
    ctx.user_data["card"] = card_type

    pkg = ctx.user_data.get("package", "")

    await query.edit_message_text(
        f"✅ Tanlangan: *{pkg}*\n\n"
        f"📌 Quyidagi kartaga to'lov qiling:\n\n"
        f"```\n{card_info}\n```\n\n"
        f"⚠️ To'lovdan so'ng *Player ID* ingizni yuboring:",
        parse_mode="Markdown"
    )
    return ENTER_PLAYER_ID

# ===== PLAYER ID =====
async def player_id_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    player_id = update.message.text.strip()
    ctx.user_data["player_id"] = player_id
    pkg = ctx.user_data.get("package", "")

    await update.message.reply_text(
        f"✅ Player ID: `{player_id}`\n\n"
        f"📸 Endi *to'lov chekini* (screenshot) yuboring:",
        parse_mode="Markdown"
    )
    return SEND_CHECK

# ===== CHEK QABUL QILISH =====
async def check_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pkg = ctx.user_data.get("package", "Noma'lum")
    player_id = ctx.user_data.get("player_id", "Noma'lum")
    card = ctx.user_data.get("card", "Noma'lum")

    # Adminga xabar
    order_id = f"{user.id}_{update.message.message_id}"
    ctx.bot_data.setdefault("orders", {})[order_id] = {
        "user_id": user.id,
        "username": user.username or user.first_name,
        "package": pkg,
        "player_id": player_id,
        "card": card,
        "status": "pending"
    }

    admin_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{order_id}"),
         InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{order_id}")]
    ])

    admin_msg = (
        f"🔔 *Yangi buyurtma!*\n\n"
        f"👤 Mijoz: @{user.username or user.first_name} (`{user.id}`)\n"
        f"💎 Paket: *{pkg}*\n"
        f"🎮 Player ID: `{player_id}`\n"
        f"💳 Karta: {card.upper()}\n\n"
        f"📸 Chek yuqorida 👆"
    )

    # Chekni adminga yuborish
    if update.message.photo:
        await ctx.bot.send_photo(
            ADMIN_ID,
            update.message.photo[-1].file_id,
            caption=admin_msg,
            parse_mode="Markdown",
            reply_markup=admin_kb
        )
    elif update.message.document:
        await ctx.bot.send_document(
            ADMIN_ID,
            update.message.document.file_id,
            caption=admin_msg,
            parse_mode="Markdown",
            reply_markup=admin_kb
        )
    else:
        await ctx.bot.send_message(
            ADMIN_ID,
            admin_msg + f"\n\n⚠️ Chek: {update.message.text}",
            parse_mode="Markdown",
            reply_markup=admin_kb
        )

    # Mijozga xabar
    await update.message.reply_text(
        "✅ *Buyurtmangiz qabul qilindi!*\n\n"
        "⏳ Admin tekshirib, 5-15 daqiqa ichida UC yuboradi.\n"
        "📞 Savol bo'lsa: @RuzoUC",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ===== ADMIN: TASDIQLASH =====
async def confirm_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    order_id = query.data.replace("confirm_", "")
    orders = ctx.bot_data.get("orders", {})
    order = orders.get(order_id)

    if not order:
        await query.edit_message_caption("⚠️ Buyurtma topilmadi.")
        return

    # Mijozga xabar
    await ctx.bot.send_message(
        order["user_id"],
        f"🎉 *UC yuborildi!*\n\n"
        f"💎 {order['package']}\n"
        f"🎮 Player ID: `{order['player_id']}`\n\n"
        f"O'yin qilishingiz muborak! 🏆\n"
        f"Yana xarid uchun /start",
        parse_mode="Markdown"
    )

    orders[order_id]["status"] = "confirmed"
    caption = query.message.caption or ""
    await query.edit_message_caption(
        caption + "\n\n✅ *TASDIQLANDI*",
        parse_mode="Markdown"
    )

# ===== ADMIN: RAD ETISH =====
async def reject_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    order_id = query.data.replace("reject_", "")
    orders = ctx.bot_data.get("orders", {})
    order = orders.get(order_id)

    if not order:
        await query.edit_message_caption("⚠️ Buyurtma topilmadi.")
        return

    await ctx.bot.send_message(
        order["user_id"],
        "❌ *Buyurtmangiz rad etildi.*\n\n"
        "Sabab: To'lov tasdiqlanmadi.\n"
        "Savol bo'lsa: @RuzoUC",
        parse_mode="Markdown"
    )

    orders[order_id]["status"] = "rejected"
    caption = query.message.caption or ""
    await query.edit_message_caption(
        caption + "\n\n❌ *RAD ETILDI*",
        parse_mode="Markdown"
    )

# ===== ORQAGA =====
async def back_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [[InlineKeyboardButton("💎 UC Sotib olish", callback_data="buy")],
          [InlineKeyboardButton("📞 Admin", url="https://t.me/RuzoUC")]]
    await query.edit_message_text(
        "🎮 *RuzoUC Bot*\n\nUC sotib olish uchun tugmani bosing:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return ConversationHandler.END

async def my_orders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📋 Buyurtmalar tarixi hozircha mavjud emas.\n\n"
        "Yangi buyurtma uchun /start",
        parse_mode="Markdown"
    )

# ===== MAIN =====
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(buy, pattern="^buy$")],
        states={
            SELECT_PACKAGE: [CallbackQueryHandler(package_selected, pattern="^pkg_")],
            SELECT_CARD: [
                CallbackQueryHandler(card_selected, pattern="^card_"),
                CallbackQueryHandler(buy, pattern="^buy$"),
            ],
            ENTER_PLAYER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, player_id_received)],
            SEND_CHECK: [MessageHandler(filters.PHOTO | filters.Document.ALL | filters.TEXT, check_received)],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(confirm_order, pattern="^confirm_"))
    app.add_handler(CallbackQueryHandler(reject_order, pattern="^reject_"))
    app.add_handler(CallbackQueryHandler(back_start, pattern="^back_start$"))
    app.add_handler(CallbackQueryHandler(my_orders, pattern="^my_orders$"))

    print("✅ Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
