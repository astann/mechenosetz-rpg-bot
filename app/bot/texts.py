"""Тексты сообщений для игрока (без клавиатур)."""

from __future__ import annotations

import time

from app.game.dungeons import dungeon_by_id
from app.shop import equipment_bonuses


def inventory_text(inv: list[dict], equipped: dict) -> str:
    lines = ["🎒 <b>Инвентарь</b>\n"]
    w = equipped.get("weapon")
    a = equipped.get("armor")
    if isinstance(w, dict):
        attack = int(w.get("attack", 0))
        lines.append(f"Оружие: {w.get('name', '?')} (атака {attack})")
    else:
        lines.append("Оружие: нет")
    if isinstance(a, dict):
        lines.append(f"Броня: {a.get('name', '?')} (+{a.get('defense', 0)} защ.)")
    else:
        lines.append("Броня: нет")
    lines.append("")
    if not inv:
        lines.append("Рюкзак пуст.")
        return "\n".join(lines)
    lines.append("Предметы:")
    for it in inv:
        if it.get("kind") == "item":
            lines.append(f"• {it.get('name', '?')} (+{it.get('value', 0)} HP)")
        else:
            lines.append(f"• {it.get('name', '?')}")
    return "\n".join(lines)


def status_text(u: dict) -> str:
    df, wm = equipment_bonuses(u.get("equipped") or {})
    eq_line = ""
    if df or wm:
        eq_line = f"Экипировка: защита −{df} урона, атака −{wm} урона.\n"
    name = str(u.get("player_name") or "Безымянный")
    base = (
        f"Имя: {name}\n"
        f"Уровень: {u['level']}\n"
        f"Опыт: {u['xp']}\n"
        f"Золото: {u['gold']}\n"
        f"HP: {u['hp_current']} / {u['hp_max']}\n"
        f"{eq_line}"
    )
    rest = u.get("rest")
    if rest:
        end = float(rest["end_ts"])
        end_label = time.strftime("%d.%m %H:%M UTC", time.gmtime(int(end)))
        rem = max(0.0, end - time.time())
        if rem <= 60:
            left_txt = "скоро полное восстановление"
        elif rem < 3600:
            left_txt = f"осталось ≈ {int(rem // 60)} мин"
        else:
            left_txt = f"осталось ≈ {rem / 3600:.1f} ч"
        base += (
            f"\n😴 <b>Отдых:</b> герой спит до {end_label} ({left_txt}). "
            "Полное HP после полного сна; досрочное пробуждение без лечения.\n"
        )
    exp = u.get("expedition")
    if not exp:
        return base + "\nЭкспедиция: не активна"
    did = exp["dungeon_id"]
    d = dungeon_by_id(str(did))
    title = d.title if d else str(did)
    return base + f"\nЭкспедиция активна: {title}\nСтолкновений: {exp['encounters']}"
