from __future__ import annotations


def max_open_act(u: dict) -> int:
    return (
        4
        if bool(u.get("fourth_act_unlocked"))
        else 3
        if bool(u.get("third_act_unlocked"))
        else 2
        if bool(u.get("next_act_unlocked"))
        else 1
    )


def effective_act(u: dict) -> int:
    act = int(u.get("selected_act", 1) or 1)
    if act < 1:
        act = 1
    return min(act, max_open_act(u))


def chapel_nav_title(u: dict) -> str:
    """Подпись кнопки и заголовок экрана: во 3 акте — священник братства."""
    if effective_act(u) == 3 and max_open_act(u) >= 3:
        return "Священник Братства"
    return "Разрушенная Часовня"


def chapel_enabled(u: dict) -> bool:
    act = effective_act(u)
    mo = max_open_act(u)
    return (act == 2 and mo >= 2) or (act == 3 and mo >= 3)


def order_enabled(u: dict) -> bool:
    """Братство Меча — только во 3 акте (и при открытом 3 акте)."""
    return effective_act(u) == 3 and max_open_act(u) >= 3

