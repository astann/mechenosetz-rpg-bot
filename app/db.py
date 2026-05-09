from __future__ import annotations

import json
import uuid
from typing import Any

import aiosqlite

from app.config import DATA_DIR, DB_PATH

SCHEMA_USERS = """
CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  username TEXT,
  level INTEGER NOT NULL DEFAULT 1,
  xp INTEGER NOT NULL DEFAULT 0,
  gold INTEGER NOT NULL DEFAULT 0,
  hp_max INTEGER NOT NULL DEFAULT 100,
  hp_current INTEGER NOT NULL DEFAULT 100,
  expedition_json TEXT,
  inventory_json TEXT NOT NULL DEFAULT '[]',
  equipped_json TEXT NOT NULL DEFAULT '{}'
);
"""

SCHEMA_SHOP = """
CREATE TABLE IF NOT EXISTS shop_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  day TEXT NOT NULL DEFAULT '',
  spin TEXT NOT NULL DEFAULT '',
  items_json TEXT NOT NULL DEFAULT '[]'
);
"""

SCHEMA_WORLD = """
CREATE TABLE IF NOT EXISTS world_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  black_wall_hp INTEGER NOT NULL DEFAULT 3000
);
"""

_PLAYERS_WIPE_MARKER = DATA_DIR / ".mechenosetz_players_cleared_v1"


async def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(SCHEMA_USERS)
        await db.execute(SCHEMA_SHOP)
        await db.execute(SCHEMA_WORLD)
        cur = await db.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in await cur.fetchall()}
        if "inventory_json" not in cols:
            await db.execute(
                "ALTER TABLE users ADD COLUMN inventory_json TEXT NOT NULL DEFAULT '[]'"
            )
        if "equipped_json" not in cols:
            await db.execute(
                "ALTER TABLE users ADD COLUMN equipped_json TEXT NOT NULL DEFAULT '{}'"
            )
        if "rest_json" not in cols:
            await db.execute("ALTER TABLE users ADD COLUMN rest_json TEXT")
        if "fishing_json" not in cols:
            await db.execute("ALTER TABLE users ADD COLUMN fishing_json TEXT")
        if "chapel_json" not in cols:
            await db.execute("ALTER TABLE users ADD COLUMN chapel_json TEXT")
        if "mercenary_json" not in cols:
            await db.execute("ALTER TABLE users ADD COLUMN mercenary_json TEXT")
        if "next_act_unlocked" not in cols:
            await db.execute(
                "ALTER TABLE users ADD COLUMN next_act_unlocked INTEGER NOT NULL DEFAULT 0"
            )
        if "third_act_unlocked" not in cols:
            await db.execute(
                "ALTER TABLE users ADD COLUMN third_act_unlocked INTEGER NOT NULL DEFAULT 0"
            )
        if "fourth_act_unlocked" not in cols:
            await db.execute(
                "ALTER TABLE users ADD COLUMN fourth_act_unlocked INTEGER NOT NULL DEFAULT 0"
            )
        if "selected_act" not in cols:
            await db.execute(
                "ALTER TABLE users ADD COLUMN selected_act INTEGER NOT NULL DEFAULT 1"
            )
        if "player_name" not in cols:
            await db.execute("ALTER TABLE users ADD COLUMN player_name TEXT")
        cur_shop = await db.execute("PRAGMA table_info(shop_state)")
        shop_cols = {row[1] for row in await cur_shop.fetchall()}
        if shop_cols and "spin" not in shop_cols:
            await db.execute(
                "ALTER TABLE shop_state ADD COLUMN spin TEXT NOT NULL DEFAULT ''"
            )
        await db.execute(
            "INSERT OR IGNORE INTO shop_state (id, day, spin, items_json) VALUES (1, '', '', '[]')"
        )
        await db.execute(
            "INSERT OR IGNORE INTO world_state (id, black_wall_hp) VALUES (1, 3000)"
        )
        await db.commit()

    if not _PLAYERS_WIPE_MARKER.exists():
        await clear_all_players(reset_shop=True)
        _PLAYERS_WIPE_MARKER.write_text("", encoding="utf-8")


async def ensure_user(user_id: int, username: str | None) -> dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if row:
            await db.execute(
                "UPDATE users SET username = ? WHERE user_id = ?",
                (username or "", user_id),
            )
            await db.commit()
            return await get_user(user_id)  # type: ignore
        await db.execute(
            "INSERT INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username or ""),
        )
        await db.commit()
    return await get_user(user_id)  # type: ignore


def _parse_exp(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("expedition_json must be a JSON object")
    return data


def _parse_json_list(raw: str | None) -> list[Any]:
    if not raw:
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("inventory_json must be a JSON array")
    return data


def _parse_rest(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("rest_json must be a JSON object")
    end_ts = data.get("end_ts")
    if end_ts is None:
        raise ValueError("rest_json must contain end_ts")
    return {"end_ts": float(end_ts)}


def _parse_fishing(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("fishing_json must be a JSON object")
    end_ts = data.get("end_ts")
    if end_ts is None:
        raise ValueError("fishing_json must contain end_ts")
    return {"end_ts": float(end_ts)}


def _parse_one_mercenary_row(data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if "slot" in data and data["slot"] is not None:
        out["slot"] = str(data["slot"])
    if "id" in data and data["id"] is not None:
        out["id"] = str(data["id"])
    if "title" in data and data["title"] is not None:
        out["title"] = str(data["title"])
    if "attack" in data and data["attack"] is not None:
        out["attack"] = int(data["attack"])
    if "defense" in data and data["defense"] is not None:
        out["defense"] = int(data["defense"])
    if "price" in data and data["price"] is not None:
        out["price"] = int(data["price"])
    if "heal_after_run" in data and data["heal_after_run"] is not None:
        out["heal_after_run"] = int(data["heal_after_run"])
    if "xp_bonus_run" in data and data["xp_bonus_run"] is not None:
        out["xp_bonus_run"] = int(data["xp_bonus_run"])
    if "hp_bonus" in data and data["hp_bonus"] is not None:
        out["hp_bonus"] = int(data["hp_bonus"])
    if not out.get("slot"):
        out["slot"] = str(uuid.uuid4())
    return out


def _parse_mercenary_roster(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    data = json.loads(raw)
    if isinstance(data, list):
        return [_parse_one_mercenary_row(x) for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        one = _parse_one_mercenary_row(data)
        return [one] if one else []
    raise ValueError("mercenary_json must be a JSON array or object")


def _parse_chapel(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("chapel_json must be a JSON object")
    out: dict[str, Any] = {}
    if "strength" in data and data["strength"] is not None:
        out["strength"] = bool(data["strength"])
    if "defense" in data and data["defense"] is not None:
        out["defense"] = bool(data["defense"])
    if "loot" in data and data["loot"] is not None:
        out["loot"] = bool(data["loot"])
    return out


def _parse_json_dict(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("equipped_json must be a JSON object")
    return data


async def get_user(user_id: int) -> dict[str, Any] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if not row:
            return None
        u = dict(row)
        u["expedition"] = _parse_exp(u.get("expedition_json"))
        u.pop("expedition_json", None)
        u["inventory"] = _parse_json_list(u.get("inventory_json"))
        u.pop("inventory_json", None)
        u["equipped"] = _parse_json_dict(u.get("equipped_json"))
        u.pop("equipped_json", None)
        rj = u.get("rest_json")
        u["rest"] = _parse_rest(rj) if rj else None
        u.pop("rest_json", None)
        fj = u.get("fishing_json")
        u["fishing"] = _parse_fishing(fj) if fj else None
        u.pop("fishing_json", None)
        cj = u.get("chapel_json")
        u["chapel"] = _parse_chapel(cj) if cj else None
        u.pop("chapel_json", None)
        mj = u.get("mercenary_json")
        u["mercenaries"] = _parse_mercenary_roster(mj) if mj else []
        u.pop("mercenary_json", None)
        u["next_act_unlocked"] = bool(int(u.get("next_act_unlocked", 0) or 0))
        u["third_act_unlocked"] = bool(int(u.get("third_act_unlocked", 0) or 0))
        u["fourth_act_unlocked"] = bool(int(u.get("fourth_act_unlocked", 0) or 0))
        u["selected_act"] = int(u.get("selected_act", 1) or 1)
        return u


async def update_user(
    user_id: int,
    *,
    level: int | None = None,
    xp: int | None = None,
    gold: int | None = None,
    hp_current: int | None = None,
    hp_max: int | None = None,
    expedition: dict[str, Any] | None = None,
    clear_expedition: bool = False,
    inventory: list[dict[str, Any]] | None = None,
    equipped: dict[str, Any] | None = None,
    rest: dict[str, Any] | None = None,
    clear_rest: bool = False,
    fishing: dict[str, Any] | None = None,
    clear_fishing: bool = False,
    chapel: dict[str, Any] | None = None,
    clear_chapel: bool = False,
    mercenary: list[dict[str, Any]] | dict[str, Any] | None = None,
    clear_mercenary: bool = False,
    next_act_unlocked: bool | None = None,
    third_act_unlocked: bool | None = None,
    fourth_act_unlocked: bool | None = None,
    selected_act: int | None = None,
    player_name: str | None = None,
) -> None:
    fields: list[str] = []
    values: list[Any] = []
    if level is not None:
        fields.append("level = ?")
        values.append(level)
    if xp is not None:
        fields.append("xp = ?")
        values.append(xp)
    if gold is not None:
        fields.append("gold = ?")
        values.append(gold)
    if hp_current is not None:
        fields.append("hp_current = ?")
        values.append(hp_current)
    if hp_max is not None:
        fields.append("hp_max = ?")
        values.append(hp_max)
    if clear_expedition:
        fields.append("expedition_json = NULL")
    elif expedition is not None:
        fields.append("expedition_json = ?")
        values.append(json.dumps(expedition, ensure_ascii=False))
    if inventory is not None:
        fields.append("inventory_json = ?")
        values.append(json.dumps(inventory, ensure_ascii=False))
    if equipped is not None:
        fields.append("equipped_json = ?")
        values.append(json.dumps(equipped, ensure_ascii=False))
    if clear_rest:
        fields.append("rest_json = NULL")
    elif rest is not None:
        fields.append("rest_json = ?")
        values.append(json.dumps(rest, ensure_ascii=False))
    if clear_fishing:
        fields.append("fishing_json = NULL")
    elif fishing is not None:
        fields.append("fishing_json = ?")
        values.append(json.dumps(fishing, ensure_ascii=False))
    if clear_chapel:
        fields.append("chapel_json = NULL")
    elif chapel is not None:
        fields.append("chapel_json = ?")
        values.append(json.dumps(chapel, ensure_ascii=False))
    if clear_mercenary:
        fields.append("mercenary_json = NULL")
    elif mercenary is not None:
        payload: list[dict[str, Any]] | dict[str, Any] = mercenary
        if isinstance(mercenary, dict):
            payload = [mercenary]
        fields.append("mercenary_json = ?")
        values.append(json.dumps(payload, ensure_ascii=False))
    if next_act_unlocked is not None:
        fields.append("next_act_unlocked = ?")
        values.append(1 if next_act_unlocked else 0)
    if third_act_unlocked is not None:
        fields.append("third_act_unlocked = ?")
        values.append(1 if third_act_unlocked else 0)
    if fourth_act_unlocked is not None:
        fields.append("fourth_act_unlocked = ?")
        values.append(1 if fourth_act_unlocked else 0)
    if selected_act is not None:
        fields.append("selected_act = ?")
        values.append(int(selected_act))
    if player_name is not None:
        fields.append("player_name = ?")
        values.append(player_name)
    if not fields:
        return
    values.append(user_id)
    sql = f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(sql, values)
        await db.commit()


async def users_with_active_expedition() -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM users WHERE expedition_json IS NOT NULL"
        )
        rows = await cur.fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        u = dict(row)
        u["expedition"] = _parse_exp(u.get("expedition_json"))
        u.pop("expedition_json", None)
        u["inventory"] = _parse_json_list(u.get("inventory_json"))
        u.pop("inventory_json", None)
        u["equipped"] = _parse_json_dict(u.get("equipped_json"))
        u.pop("equipped_json", None)
        rj = u.get("rest_json")
        u["rest"] = _parse_rest(rj) if rj else None
        u.pop("rest_json", None)
        fj = u.get("fishing_json")
        u["fishing"] = _parse_fishing(fj) if fj else None
        u.pop("fishing_json", None)
        cj = u.get("chapel_json")
        u["chapel"] = _parse_chapel(cj) if cj else None
        u.pop("chapel_json", None)
        mj = u.get("mercenary_json")
        u["mercenaries"] = _parse_mercenary_roster(mj) if mj else []
        u.pop("mercenary_json", None)
        u["next_act_unlocked"] = bool(int(u.get("next_act_unlocked", 0) or 0))
        u["third_act_unlocked"] = bool(int(u.get("third_act_unlocked", 0) or 0))
        u["fourth_act_unlocked"] = bool(int(u.get("fourth_act_unlocked", 0) or 0))
        u["selected_act"] = int(u.get("selected_act", 1) or 1)
        if u["expedition"]:
            out.append(u)
    return out


async def users_with_rest_finished(now_ts: float) -> list[dict[str, Any]]:
    """Пользователи, у которых отдых закончился по времени (нужно полное восстановление)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT user_id FROM users WHERE rest_json IS NOT NULL")
        ids = [int(row[0]) for row in await cur.fetchall()]
    out: list[dict[str, Any]] = []
    for uid in ids:
        u = await get_user(uid)
        if not u:
            continue
        rest = u.get("rest")
        if rest and float(rest["end_ts"]) <= now_ts:
            out.append(u)
    return out


async def users_with_fishing_finished(now_ts: float) -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT user_id FROM users WHERE fishing_json IS NOT NULL")
        ids = [int(row[0]) for row in await cur.fetchall()]
    out: list[dict[str, Any]] = []
    for uid in ids:
        u = await get_user(uid)
        if not u:
            continue
        fishing = u.get("fishing")
        if fishing and float(fishing["end_ts"]) <= now_ts:
            out.append(u)
    return out


async def get_shop_state() -> tuple[str, list[dict[str, Any]]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT day, items_json FROM shop_state WHERE id = 1"
        )
        row = await cur.fetchone()
        if not row:
            return "", []
        day = str(row["day"] or "")
        raw = row["items_json"] or "[]"
        items = json.loads(raw)
        if not isinstance(items, list):
            raise ValueError("shop items_json must be a JSON array")
        return day, [x for x in items if isinstance(x, dict)]


async def set_shop_state(day: str, items: list[dict[str, Any]]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE shop_state SET day = ?, spin = '', items_json = ? WHERE id = 1",
            (day, json.dumps(items, ensure_ascii=False)),
        )
        await db.commit()


async def clear_all_players(*, reset_shop: bool = True) -> None:
    """Удалить всех пользователей. По желанию сбросить глобальную витрину магазина."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users")
        if reset_shop:
            await db.execute(
                "UPDATE shop_state SET day = '', spin = '', items_json = '[]' WHERE id = 1"
            )
        await db.commit()


async def get_black_wall_hp() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT black_wall_hp FROM world_state WHERE id = 1")
        row = await cur.fetchone()
        if not row:
            return 0
        return int(row[0] or 0)


async def damage_black_wall(amount: int) -> int:
    dmg = max(0, int(amount))
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT black_wall_hp FROM world_state WHERE id = 1")
        row = await cur.fetchone()
        hp = int(row[0] or 0) if row else 0
        hp_new = max(0, hp - dmg)
        await db.execute(
            "UPDATE world_state SET black_wall_hp = ? WHERE id = 1",
            (hp_new,),
        )
        await db.commit()
    return hp_new


async def unlock_act4_for_all() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET fourth_act_unlocked = 1")
        await db.commit()


async def all_user_ids() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users")
        rows = await cur.fetchall()
    return [int(r[0]) for r in rows]
