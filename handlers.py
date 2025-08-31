# handlers.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS, ADMIN_CODE, TEST_MAX_QUESTIONS
from db import (
    add_test, add_question, count_questions, list_tests, delete_test,
    add_link, delete_link, list_links, get_available_link, increment_link_users,
    save_result, get_user, list_results, get_questions, add_user_if_not_exists, update_user_group_and_score
)
from keyboards import main_menu, test_selection_keyboard, answer_buttons
from utils import send_question, safe_text, finish as utils_finish

logger = logging.getLogger("handlers")

# ==========================
# Admin: Test yaratish
# ==========================
async def cmd_testyaratish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text("⛔ Siz admin emassiz.")
        return
    context.user_data.clear()
    context.user_data["mode"] = "awaiting_admin_code"
    await update.message.reply_text("🔑 Iltimos admin-kodni kiriting:")

async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return
    context.user_data.clear()
    await update.message.reply_text("✅ Test yaratish yakunlandi.")

async def cmd_deletetest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return
    if not context.args:
        await update.message.reply_text("❌ Foydalanish: /deletetest TEST_ID")
        return
    try:
        tid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID butun son bo‘lishi kerak.")
        return
    delete_test(tid)
    await update.message.reply_text(f"✅ Test (id={tid}) o‘chirildi.")

async def cmd_showtests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return
    tests = list_tests()
    if not tests:
        await update.message.reply_text("❌ Testlar mavjud emas.")
        return
    text = "📋 Testlar:\n"
    for t in tests:
        try:
            tid, name = t["id"], t["name"]
        except TypeError:
            tid, name = t[0], t[1]
        text += f"{tid}) {safe_text(name)}\n"
    await update.message.reply_text(text)

# ==========================
# Admin: Links
# ==========================
async def cmd_addlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text("⛔ Siz admin emassiz.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Foydalanish: /addlink A1 https://t.me/... [max_users]")
        return
    group = context.args[0].upper()
    url = context.args[1]
    maxu = None
    if len(context.args) >= 3:
        try:
            maxu = int(context.args[2])
        except ValueError:
            maxu = None
    add_link(group, url, maxu or None)
    await update.message.reply_text("✅ Havola qo‘shildi.")

async def cmd_dellink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return
    if not context.args:
        await update.message.reply_text("❌ Foydalanish: /dellink LINK_ID")
        return
    try:
        lid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID butun son bo‘lishi kerak.")
        return
    delete_link(lid)
    await update.message.reply_text("✅ Havola o‘chirildi.")

async def cmd_showlinks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return
    rows = list_links()
    if not rows:
        await update.message.reply_text("Havolalar topilmadi.")
        return
    text = "📌 Havolalar:\n"
    for r in rows:
        text += f"{r['id']}) {r['group_type']} — {r['url']} ({r['current_users']}/{r['max_users'] or '∞'})\n"
    await update.message.reply_text(text)

# ==========================
# User: Test boshlash
# ==========================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tests = list_tests()
    if not tests:
        await update.message.reply_text("❌ Hozircha testlar mavjud emas.")
        return
    buttons = [(t["id"], t["name"]) for t in tests]
    kb = test_selection_keyboard(buttons)
    await update.message.reply_text(
        "Iltimos ishlamoqchi bo‘lgan testni tanlang:", 
        reply_markup=kb
    )

async def handle_starttest_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        tid = int(q.data.split(":", 1)[1])
    except:
        await q.message.reply_text("❌ Xato test id.")
        return
    questions = get_questions(tid)
    if not questions:
        await q.message.reply_text("❌ Bu testda savollar mavjud emas.")
        return
    ud = context.user_data
    ud.clear()
    ud["test_id"] = tid
    ud["questions"] = questions
    ud["current_index"] = 0
    ud["score"] = 0
    add_user_if_not_exists(q.from_user.id, q.from_user.full_name or "", q.from_user.username or "")
    await send_question(update, context)

# ==========================
# Admin + Menu Handler
# ==========================
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    ud = context.user_data

    # Admin code flow
    if ud.get("mode") == "awaiting_admin_code":
        if text == ADMIN_CODE:
            ud["mode"] = "awaiting_test_name"
            await update.message.reply_text("✅ Kod to‘g‘ri. Test nomini kiriting (max 40):")
        else:
            await update.message.reply_text("❌ Kod noto‘g‘ri.")
        return

    if ud.get("mode") == "awaiting_test_name":
        tid = add_test(text[:200])
        ud["test_id"] = tid
        ud["mode"] = "awaiting_question"
        ud["qcount"] = 0
        await update.message.reply_text(f"✅ Test yaratildi (id={tid}). Endi 1-savolni kiriting:")
        return

    if ud.get("mode") == "awaiting_question":
        ud["current_question"] = text
        ud["mode"] = "awaiting_option_a"
        await update.message.reply_text("A variantni kiriting:")
        return
    if ud.get("mode") == "awaiting_option_a":
        ud["option_a"] = text
        ud["mode"] = "awaiting_option_b"
        await update.message.reply_text("B variantni kiriting:")
        return
    if ud.get("mode") == "awaiting_option_b":
        ud["option_b"] = text
        ud["mode"] = "awaiting_option_c"
        await update.message.reply_text("C variantni kiriting:")
        return
    if ud.get("mode") == "awaiting_option_c":
        ud["option_c"] = text
        ud["mode"] = "awaiting_option_d"
        await update.message.reply_text("D variantni kiriting:")
        return
    if ud.get("mode") == "awaiting_option_d":
        ud["option_d"] = text
        ud["mode"] = "awaiting_correct"
        await update.message.reply_text("To‘g‘ri javobni kiriting (A/B/C/D):")
        return
    if ud.get("mode") == "awaiting_correct":
        correct = text.strip().upper()
        if correct not in ("A","B","C","D"):
            await update.message.reply_text("❌ To‘g‘ri javob: A, B, C yoki D bo‘lishi kerak.")
            return
        qcount = ud.get("qcount",0)
        if qcount >= TEST_MAX_QUESTIONS:
            ud["mode"] = None
            await update.message.reply_text(f"❌ Savol maksimal {TEST_MAX_QUESTIONS} ga yetdi. /done bilan tugating.")
            return
        add_question(
            ud["test_id"],
            ud["current_question"],
            ud["option_a"],
            ud["option_b"],
            ud["option_c"],
            ud["option_d"],
            correct
        )
        ud["qcount"] = qcount + 1
        ud["mode"] = "awaiting_question"
        await update.message.reply_text(f"✅ Savol qo‘shildi. Umumiy savollar: {ud['qcount']}. Keyingi savolni kiriting yoki /done yozing.")
        return

    # Main menu
    if text == "🧪 Testni boshlash":
        return await cmd_start(update, context)
    if text == "📊 Ballarim":
        u = get_user(update.effective_user.id)
        if not u:
            return await update.message.reply_text("Siz hali test ishlamadingiz.")
        link = None
        if u.get("link_id"):
            lks = list_links()
            for l in lks:
                if l["id"] == u["link_id"]:
                    link = l["url"]
                    break
        username = u.get("username") or u.get("full_name") or update.effective_user.id
        await update.message.reply_text(f"{username}: {u.get('score',0)} ball\nGuruh: {u.get('group_type')}\nLink: {link or '—'}")
        return
    if text == "⏹ To‘xtatish":
        ud.clear()
        return await update.message.reply_text("Test bekor qilindi.")
    if text == "🆕 Test yaratish":
        return await cmd_testyaratish(update, context)
    if text == "🔗 Link qo‘shish":
        if update.effective_user.id in ADMIN_IDS:
            return await update.message.reply_text("Link qo‘shish uchun: /addlink A1 https://t.me/... [max_users]")
        return await update.message.reply_text("⛔ Siz admin emassiz.")
    
    await update.message.reply_text("🤖 Menyudan tanlang yoki admin bo‘lsangiz /testyaratish bilan test qo‘shing.")

# ==========================
# Inline answer callback
# ==========================
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ud = context.user_data
    questions = ud.get("questions", [])
    idx = ud.get("current_index", 0)
    parts = q.data.split(":",1)
    choice = parts[1].upper() if len(parts)>1 else parts[0].upper()
    if not questions or idx >= len(questions):
        await q.message.reply_text("❌ Savol topilmadi yoki test yakunlangan.")
        ud.clear()
        return
    qrow = questions[idx]
    correct = qrow["correct"].upper()
    if choice == correct:
        ud["score"] = ud.get("score",0)+1
        await q.message.reply_text("✅ To‘g‘ri!")
    else:
        await q.message.reply_text(f"❌ Noto‘g‘ri. To‘g‘ri javob: {correct}")
    ud["current_index"] = idx + 1
    if ud["current_index"] < len(questions):
        await send_question(update, context)
    else:
        await utils_finish(update, context)

# ==========================
# Stats & Help
# ==========================
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    rows = list_results()
    if not rows:
        await update.message.reply_text("📊 Hali natijalar mavjud emas.")
        return
    text = "📊 Statistik natijalar:\n\n"
    for r in rows:
        user = get_user(r.get('user_id'))
        username = user.get('username') or user.get('full_name') or r.get('user_id')
        link = None
        if r.get("link_id"):
            lks = list_links()
            for l in lks:
                if l["id"] == r["link_id"]:
                    link = l["url"]
                    break
        text += f"👤 {username} — {r.get('score')} ball, Link: {link or '—'}\n"
    await update.message.reply_text(text)

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 Bot komandalar:\n\n"
        "🧑‍🎓 Foydalanuvchilar:\n"
        "  • 🧪 Testni boshlash\n"
        "  • 📊 Ballarim\n"
        "  • ⏹ To‘xtatish\n\n"
        "🛠 Admin:\n"
        "  • /testyaratish – test yaratish\n"
        "  • /done – testni tugatish\n"
        "  • /deletetest ID – testni o‘chirish\n"
        "  • /showtests – testlar ro‘yxati\n"
        "  • /addlink A1|B1 https://t.me/... [max] – link qo‘shish\n"
        "  • /dellink ID – link o‘chirish\n"
        "  • /showlinks – linklar ro‘yxati\n"
        "  • /stats – umumiy statistika\n"
    )
    await update.message.reply_text(text)
