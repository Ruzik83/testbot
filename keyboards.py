from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict

def main_menu(is_admin: bool = False):
    """
    Foydalanuvchi uchun asosiy menyu. Admin uchun qo'shimcha tugmalar.
    """
    buttons = [
        [KeyboardButton("🧪 Testni boshlash")],
        [KeyboardButton("📊 Ballarim"), KeyboardButton("⏹ To'xtatish")]
    ]
    if is_admin:
        buttons.append([KeyboardButton("🆕 Test yaratish")])
        buttons.append([KeyboardButton("🔗 Link qo'shish")])
        buttons.append([KeyboardButton("📋 Testlar ro'yxati")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def test_selection_keyboard(tests: List[Dict]):
    """
    Inline tugmalar bilan testni tanlash.
    """
    buttons = []
    for t in tests:
        tid = t["id"]
        name = t["name"]
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"starttest:{tid}")])
    return InlineKeyboardMarkup(buttons)

def answer_buttons():
    """
    Javob variantlari tugmalari (A/B/C/D).
    """
    buttons = [
        [InlineKeyboardButton("A", callback_data="answer:A"), InlineKeyboardButton("B", callback_data="answer:B")],
        [InlineKeyboardButton("C", callback_data="answer:C"), InlineKeyboardButton("D", callback_data="answer:D")]
    ]
    return InlineKeyboardMarkup(buttons)
