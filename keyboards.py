from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Union

# ===============================
# Asosiy menyu
# ===============================
def main_menu(is_admin: bool = False):
    buttons = [
        [KeyboardButton("🧪 Testni boshlash")],
        [KeyboardButton("📊 Ballarim"), KeyboardButton("⏹ To'xtatish")]
    ]
    if is_admin:
        buttons.append([KeyboardButton("🆕 Test yaratish")])
        buttons.append([KeyboardButton("🔗 Link qo'shish")])
        buttons.append([KeyboardButton("📋 Testlar ro'yxati")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ===============================
# Testni tanlash tugmalari
# ===============================
def test_selection_keyboard(tests: List[Union[Dict, tuple]]):
    buttons = []
    for t in tests:
        if isinstance(t, dict):
            tid, name = t["id"], t["name"]
        elif isinstance(t, (tuple, list)) and len(t) >= 2:
            tid, name = t[0], t[1]
        else:
            continue
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"starttest:{tid}")])
    return InlineKeyboardMarkup(buttons)

# ===============================
# Javob variantlari
# ===============================
def answer_buttons():
    buttons = [
        [InlineKeyboardButton("A", callback_data="answer:A"), InlineKeyboardButton("B", callback_data="answer:B")],
        [InlineKeyboardButton("C", callback_data="answer:C"), InlineKeyboardButton("D", callback_data="answer:D")]
    ]
    return InlineKeyboardMarkup(buttons)
