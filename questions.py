import json, os
from config import DATA_FILE

def load_questions():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_questions(questions):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

def add_question(q_text, options, correct_idx):
    questions = load_questions()
    if len(questions) >= 40:
        return False, "❌ Bitta test to‘plamida maksimal 40 ta savol bo‘ladi."
    questions.append({
        "question": q_text,
        "options": options,
        "answer": correct_idx
    })
    save_questions(questions)
    return True, "✅ Savol qo‘shildi."

def delete_question(index):
    questions = load_questions()
    if 0 <= index < len(questions):
        questions.pop(index)
        save_questions(questions)
        return True, "✅ Savol o‘chirildi."
    return False, "❌ Noto‘g‘ri index."
