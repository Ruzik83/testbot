import json, os
from config import GROUP_FILE

def load_groups():
    if not os.path.exists(GROUP_FILE):
        return {"A": [], "B": []}
    with open(GROUP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_groups(data):
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_group(level: str, name: str, link: str):
    groups = load_groups()
    groups.setdefault(level, [])
    groups[level].append({"name": name, "link": link, "students": 0})
    save_groups(groups)
    return f"✅ Guruh qo‘shildi: {name}"

def delete_group(name: str):
    groups = load_groups()
    for level in groups:
        groups[level] = [g for g in groups[level] if g["name"] != name]
    save_groups(groups)
    return f"✅ Guruh o‘chirildi: {name}"

def assign_group(level: str):
    groups = load_groups()
    for g in groups.get(level, []):
        if g["students"] < 20:
            g["students"] += 1
            save_groups(groups)
            return g["link"]
    return "❌ Bu daraja uchun bo‘sh joy yo‘q."

def list_groups():
    groups = load_groups()
    lines = []
    for level, arr in groups.items():
        for g in arr:
            lines.append(f"{g['name']} ({level}) — {g['students']}/20")
    return "\n".join(lines) if lines else "❌ Guruh mavjud emas."
