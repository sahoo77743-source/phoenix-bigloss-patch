#!/usr/bin/env python3
"""Block one symbol for 6 hours when its close is worse than -1R."""
import os
import shutil
import py_compile

TARGET = "main.py"
BACKUP = "main.py.bak_bigloss"

REPLACEMENTS = [
(
"""LOSS_REENTRY_SEC = 2700                     # 45 min after a forced loss close
""",
"""LOSS_REENTRY_SEC = 2700                     # 45 min after a forced loss close
BIG_LOSS_REENTRY_SEC = 21600                # 6h after a close worse than -1R
"""
),
(
"""def clear_symbol_occupancy(symbol: str, force: bool = False, reason: str = None):
    tag = "INVALIDATED" if reason and "INVALIDATION" in str(reason) else "CLOSED"
    occupied_symbols[symbol] = {"strategy": tag, "side": None, "ts": now_utc(), "reason": reason}
""",
"""def clear_symbol_occupancy(symbol: str, force: bool = False, reason: str = None, closed_r: float = None):
    tag = "INVALIDATED" if reason and "INVALIDATION" in str(reason) else "CLOSED"
    try:
        r = None if closed_r is None else float(closed_r)
    except Exception:
        r = None
    if r is not None and r < -1.0:
        tag = "BIG_LOSS"
        logger.info(f"🚫 6h block {symbol} | R={r:.2f}")
    occupied_symbols[symbol] = {"strategy": tag, "side": None, "ts": now_utc(), "reason": reason}
"""
),
(
"""            if occ.get("strategy") == "FORCE_CLOSED" and age < LOSS_REENTRY_SEC:
                continue
""",
"""            if occ.get("strategy") == "FORCE_CLOSED" and age < LOSS_REENTRY_SEC:
                continue
            if occ.get("strategy") == "BIG_LOSS" and age < BIG_LOSS_REENTRY_SEC:
                continue
"""
),
(
"""                elif occ.get("strategy") == "FORCE_CLOSED":
                    block_sec = LOSS_REENTRY_SEC
""",
"""                elif occ.get("strategy") == "FORCE_CLOSED":
                    block_sec = LOSS_REENTRY_SEC
                elif occ.get("strategy") == "BIG_LOSS":
                    block_sec = BIG_LOSS_REENTRY_SEC
"""
),
(
"""                if occ.get("strategy") == "CLOSED":
                    block_sec = SYMBOL_REENTRY_COOLDOWN_SEC
                if occ.get("strategy") == "INVALIDATED":
                    block_sec = SYMBOL_INVALIDATION_REENTRY_SEC
                if age < block_sec:
                    return False
""",
"""                if occ.get("strategy") == "CLOSED":
                    block_sec = SYMBOL_REENTRY_COOLDOWN_SEC
                if occ.get("strategy") == "INVALIDATED":
                    block_sec = SYMBOL_INVALIDATION_REENTRY_SEC
                if occ.get("strategy") == "BIG_LOSS":
                    block_sec = BIG_LOSS_REENTRY_SEC
                if age < block_sec:
                    return False
"""
),
(
"""                    clear_symbol_occupancy(symbol, force=True)
""",
"""                    clear_symbol_occupancy(symbol, force=True, closed_r=closed_r)
"""
),
(
"""                    clear_symbol_occupancy(symbol, force=True, reason=ld_reason)
""",
"""                    clear_symbol_occupancy(symbol, force=True, reason=ld_reason, closed_r=closed_r)
"""
),
(
"""                                    clear_symbol_occupancy(symbol, force=True, reason=reason)
""",
"""                                    clear_symbol_occupancy(symbol, force=True, reason=reason, closed_r=closed_r)
"""
),
]


def main():
    if not os.path.exists(TARGET):
        print(f"STOPPED missing {TARGET}")
        return
    shutil.copy2(TARGET, BACKUP)
    text = open(TARGET, encoding="utf-8").read()
    # The plain clear() lines that sit next to a real close R. Expected 5.
    plain = REPLACEMENTS[5][0]
    if text.count(plain) != 5:
        shutil.copy2(BACKUP, TARGET)
        print(f"STOPPED plain-clear count={text.count(plain)}")
        print(f"restored from {BACKUP} — bot file was not changed")
        return
    for i, (old, new) in enumerate(REPLACEMENTS, 1):
        n = text.count(old)
        expect = 5 if i == 6 else 1
        if n != expect:
            shutil.copy2(BACKUP, TARGET)
            print(f"STOPPED piece {i} count={n} expect={expect}")
            print(f"restored from {BACKUP} — bot file was not changed")
            return
        text = text.replace(old, new)
    open(TARGET, "w", encoding="utf-8").write(text)
    try:
        py_compile.compile(TARGET, doraise=True)
    except Exception as e:
        shutil.copy2(BACKUP, TARGET)
        print(f"STOPPED compile: {e}")
        print(f"restored from {BACKUP} — bot file was not changed")
        return
    print(f"DONE pieces={len(REPLACEMENTS)}")
    print(f"backup={BACKUP}")


if __name__ == "__main__":
    main()
