"""Тексты сообщений для игрока (без клавиатур)."""

from __future__ import annotations

import time

from app.game.dungeons import dungeon_by_id
from app.game.chapel import (
    CHAPEL_DEFENSE_BONUS,
    CHAPEL_LOOT_BOOST,
    CHAPEL_STRENGTH_BONUS,
    active_bonuses,
)
from app.game.mercenary_order import (
    aggregate_mercenary_stats,
    effective_hp_max_for_user,
    roster_summary_lines,
)
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
        rarity = str(it.get("rarity", ""))
        rarity_txt = ""
        if rarity == "common":
            rarity_txt = " [обычный]"
        elif rarity == "rare":
            rarity_txt = " [редкий]"
        elif rarity == "epic":
            rarity_txt = " [эпический]"
        if it.get("kind") == "item":
            lines.append(f"• {it.get('name', '?')} (+{it.get('value', 0)} HP){rarity_txt}")
        elif it.get("kind") == "weapon":
            lines.append(f"• {it.get('name', '?')} (+{it.get('attack', 0)} ат){rarity_txt}")
        elif it.get("kind") == "armor":
            lines.append(f"• {it.get('name', '?')} (+{it.get('defense', 0)} защ){rarity_txt}")
        else:
            lines.append(f"• {it.get('name', '?')}{rarity_txt}")
    return "\n".join(lines)


def status_text(u: dict) -> str:
    df, wm = equipment_bonuses(u.get("equipped") or {})
    chapel_atk, chapel_df, chapel_loot = active_bonuses(u.get("chapel"))
    total_wm = wm + chapel_atk
    total_df = df + chapel_df
    name = str(u.get("player_name") or "Безымянный")
    hp_cap_disp = effective_hp_max_for_user(u)
    base = (
        f"Имя: {name} · Уровень: {u['level']}\n"
        f"Опыт: {u['xp']} · Золото: {u['gold']}\n"
        f"HP: {u['hp_current']}/{hp_cap_disp} · +атака: {total_wm} · +защита: {total_df}\n"
    )
    if chapel_atk > 0:
        base += f"⛪ Благословение силы: +{CHAPEL_STRENGTH_BONUS}\n"
    if chapel_df > 0:
        base += f"⛪ Благословение защиты: +{CHAPEL_DEFENSE_BONUS}\n"
    if chapel_loot > 0:
        pct = int(round(CHAPEL_LOOT_BOOST * 100))
        base += f"⛪ Благодать богатств: +{pct}% к шансу трофея\n"
    exp_m = u.get("expedition")
    if isinstance(exp_m, dict) and (
        int(exp_m.get("merc_attack", 0) or 0) > 0
        or int(exp_m.get("merc_defense", 0) or 0) > 0
        or int(exp_m.get("merc_heal_after_run", 0) or 0) > 0
        or int(exp_m.get("merc_xp_bonus", 0) or 0) > 0
        or int(exp_m.get("merc_hp_bonus", 0) or 0) > 0
    ):
        ma = int(exp_m.get("merc_attack", 0) or 0)
        md = int(exp_m.get("merc_defense", 0) or 0)
        mh = int(exp_m.get("merc_heal_after_run", 0) or 0)
        mx = int(exp_m.get("merc_xp_bonus", 0) or 0)
        mhp = int(exp_m.get("merc_hp_bonus", 0) or 0)
        bits: list[str] = []
        if ma or md:
            bits.append(f"+{ma} ат, +{md} защ")
        if mhp:
            bits.append(f"+{mhp} макс. HP")
        if mh:
            bits.append(f"+{mh} HP после забега")
        if mx:
            bits.append(f"+{mx} опыта за поход")
        base += f"🛡 Отряд братства: {', '.join(bits)}.\n"
    elif u.get("mercenaries"):
        mercs = list(u["mercenaries"])
        agg = aggregate_mercenary_stats(mercs)
        lines = roster_summary_lines(mercs)
        summ = ", ".join(lines) if lines else ""
        bits2: list[str] = []
        if agg["attack"] or agg["defense"]:
            bits2.append(f"+{agg['attack']} ат, +{agg['defense']} защ")
        if agg["heal_after_run"]:
            bits2.append(f"+{agg['heal_after_run']} HP после забега")
        if agg["xp_bonus_run"]:
            bits2.append(f"+{agg['xp_bonus_run']} опыта за поход")
        if agg["hp_bonus"]:
            bits2.append(f"+{agg['hp_bonus']} макс. HP")
        base += (
            f"🛡 Отряд ({len(mercs)}): {summ}. "
            f"{', '.join(bits2)}.\n"
        )
    rest = u.get("rest")
    if rest:
        end = float(rest["end_ts"])
        end_label = time.strftime("%d.%m %H:%M", time.localtime(int(end)))
        base += (
            f"\n😴 <b>Отдых:</b> герой спит до {end_label}. "
            "Полное HP после полного сна; досрочное пробуждение без лечения.\n"
        )
    fishing = u.get("fishing")
    if fishing:
        end = float(fishing["end_ts"])
        end_label = time.strftime("%d.%m %H:%M", time.localtime(int(end)))
        base += (
            f"\n🎣 <b>Рыбалка:</b> герой на реке до {end_label}. "
            "После возвращения получит рыбу в инвентарь.\n"
        )
    exp = u.get("expedition")
    if not exp:
        return base + "\nЭкспедиция: не активна"
    did = exp["dungeon_id"]
    d = dungeon_by_id(str(did))
    title = d.title if d else str(did)
    return base + f"\nЭкспедиция активна: {title}\nСтолкновений: {exp['encounters']}"
