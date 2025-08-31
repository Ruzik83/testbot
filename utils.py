# utils.py
import html
from telegram import Update
from db import get_questions, get_available_link, increment_link_users, save_result, create_group_if_needed
from keyboards import answer_buttons
from config import A_THRESHOLD

def safe_text(text: str) -> str:
    return html.escape(text) if text else ""

async def send_question(update: Update, context):
    ud = context.user_data
    bd = context.bot_data
    test_id = ud.get("test_id")
    if not test_id:
        await update.effective_message.reply_text("❌ Test tanlanmagan.")
        return

    # cache questions in bot_data
    if "questions" not in bd or bd.get("questions_test_id") != test_id:
        questions = get_questions(test_id)
        bd["questions"] = questions
        bd["questions_test_id"] = test_id
    else:
        questions = bd["questions"]

    idx = ud.get("current_index", 0)
    if idx >= len(questions):
        await finish(update, context)
        return

    q = questions[idx]
    text = f"❓ Savol {idx+1}/{len(questions)}:\n\n{q['question']}\n\nA) {q['option_a']}\nB) {q['option_b']}\nC) {q['option_c']}\nD) {q['option_d']}"
    await update.effective_message.reply_text(text, reply_markup=answer_buttons())

async def finish(update: Update, context):
    ud = context.user_data
    bd = context.bot_data
    # determine message container
    if hasattr(update, "callback_query") and update.callback_query:
        msg_container = update.callback_query.message
        user = update.callback_query.from_user
    else:
        msg_container = update.message
        user = update.effective_user

    score = ud.get("score", 0)
    questions = bd.get("questions", [])
    total = len(questions) if questions else ud.get("total", 0)
    percent = round((score / total) * 100, 2) if total else 0.0

    # determine A or B by percent threshold
    group_letter = "A" if percent >= A_THRESHOLD else "B"

    # find available link with prefix (A1,A2... or B1,B2...)
    link_row = get_available_link(group_letter)
    created_new = False
    if not link_row:
        # create new group (A1/A2... or B1/B2...), then use it
        link_row = create_group_if_needed(group_letter)
        created_new = True

    if link_row:
        link_id = link_row["id"]
        url = link_row["url"]
        increment_link_users(link_id)
        save_result(user.id, score, total, link_id)
        # update user's group and score
        # Note: update_user_group_and_score imported in handlers will be used
        msg = (f"✅ Test tugadi!\nNatija: {score}/{total} ({percent}%)\n"
               f"Siz {group_letter} guruhiga kirdingiz.\n👉 {url}")
        if created_new:
            msg += "\n(Avtomatik yangi guruh yaratildi)"
    else:
        save_result(user.id, score, total, None)
        msg = f"✅ Test tugadi!\nNatija: {score}/{total} ({percent}%)\nHozirda {group_letter} guruhida bo'sh joy topilmadi."

    await msg_container.reply_text(msg)
    # clear session keys
    for k in ("test_id", "current_index", "score"):
        ud.pop(k, None)
